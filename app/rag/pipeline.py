from typing import AsyncIterator

from llama_index.core.llms import ChatMessage

from starlette.concurrency import run_in_threadpool

from app.models import Clause
from app.rag.chat import (
    UNSURE_RESPONSE,
    build_fast_llm,
    build_refined_search_query,
    build_search_query,
    condense_to_standalone_question,
    format_context,
    generate_answer_stream,
    split_into_questions,
    verify_answer,
)
from app.rag.applicability import keep_applicable
from app.rag.expansion import expand_clauses
from app.rag.kb_outline import get_kb_outline
from app.rag.retrieval import Passage, dedup_key, retrieve_relevant_passages

DRAFT_ATTEMPTS = 2


def _merge_passages(primary: list[Passage], extra: list[Passage]) -> list[Passage]:
    seen = {dedup_key(p) for p in primary}
    merged = list(primary)
    for passage in extra:
        key = dedup_key(passage)
        if key not in seen:
            seen.add(key)
            merged.append(passage)
    return merged


def _merge_clauses(primary: list[Clause], extra: list[Clause]) -> list[Clause]:
    seen = {c.id for c in primary}
    merged = list(primary)
    for clause in extra:
        if clause.id not in seen:
            seen.add(clause.id)
            merged.append(clause)
    return merged


def _found_labels(passages: list[Passage], clauses: list[Clause]) -> list[str]:
    labels: list[str] = []
    for passage in passages:
        label = passage.metadata.get("breadcrumb") or passage.metadata.get("title")
        if label:
            labels.append(label)
    for clause in clauses:
        if clause.breadcrumb:
            labels.append(clause.breadcrumb)
    return list(dict.fromkeys(labels))


def _build_context_block(
    passages: list[Passage], clauses: list[Clause], cross_session_context: str
) -> str:
    context_block = format_context(passages, clauses)
    if cross_session_context:
        context_block = (
            f"{context_block}\n\n[Background from earlier sessions]\n{cross_session_context}"
        )
    return context_block


async def _filter_applicable(
    applicability_questions: list[str], passages: list[Passage], clauses: list[Clause]
):
    """Run the applicability gate once PER sub-question and UNION the survivors.

    A single compound message can ask about both an ordinary situation and a
    special one (e.g. emergency work). Judging the blended question once makes
    the filter drop whichever scenario is not dominant; judging each sub-question
    separately keeps the provisions each part needs, while a purely ordinary
    question still drops conditional provisions (Bug1 stays fixed)."""
    keep_passage_keys: set = set()
    keep_clause_ids: set = set()
    for question in applicability_questions:
        kept_passages, kept_clauses = await keep_applicable(question, passages, clauses)
        keep_passage_keys.update(dedup_key(p) for p in kept_passages)
        keep_clause_ids.update(c.id for c in kept_clauses)
    passages = [p for p in passages if dedup_key(p) in keep_passage_keys]
    clauses = [c for c in clauses if c.id in keep_clause_ids]
    return passages, clauses


async def _retrieve_passages(rerank_query: str, extra_queries: list[str]) -> list[Passage]:
    return await run_in_threadpool(retrieve_relevant_passages, rerank_query, extra_queries)


async def _gather_for_subquestions(fast_llm, sub_questions: list[str]) -> list[Passage]:
    """Retrieve once PER sub-question - each reranked against its OWN intent - and
    union the passages.

    A blended compound query lets the dominant intent crowd the others out of the
    reranked top-K: e.g. an emergency sub-question floods the pool with Appendix C
    passages and EVICTS the ordinary-day meal-break clause (23.2), so the answer
    can no longer be grounded. Retrieving per sub-question and unioning keeps the
    best passages for EVERY intent. For a single-intent question this is just one
    retrieval, so behaviour is unchanged."""
    merged: list[Passage] = []
    for sub in sub_questions:
        search_query = await run_in_threadpool(build_search_query, fast_llm, sub)
        passages = await _retrieve_passages(sub, [search_query])
        merged = _merge_passages(merged, passages)
    return merged


async def _retrieve_and_filter(db, fast_llm, sub_questions: list[str]):
    passages = await _gather_for_subquestions(fast_llm, sub_questions)
    clauses = await expand_clauses(db, passages)
    return await _filter_applicable(sub_questions, passages, clauses)


async def _stream_drafts_and_verify(
    system_prompt: str,
    history: list[ChatMessage],
    message: str,
    standalone_question: str,
    context_block: str,
    kb_map: str,
) -> AsyncIterator[dict]:
    """Stream up to DRAFT_ATTEMPTS drafts. Each draft is streamed live as
    ``delta`` events; once complete it is verified (fast lane). On a passing
    verdict we emit ``final`` and stop. If a draft fails, we emit ``reset`` so
    the UI clears the unverified draft and try again. If all attempts fail we
    emit an internal ``_failed`` marker (never sent to the client)."""
    for attempt in range(DRAFT_ATTEMPTS):
        if attempt > 0:
            yield {"t": "reset"}
            yield {"t": "status", "v": "Refining your answer…"}

        draft = ""
        async for token in generate_answer_stream(
            system_prompt, history, context_block, message, kb_map, attempt
        ):
            draft += token
            yield {"t": "delta", "v": token}

        verdict = await run_in_threadpool(
            verify_answer, context_block, standalone_question, draft, kb_map, history
        )
        if verdict.passed:
            yield {"t": "final", "v": draft}
            return

    yield {"t": "_failed"}


async def stream_grounded_answer(
    db,
    history: list[ChatMessage],
    cross_session_context: str,
    system_prompt: str,
    message: str,
) -> AsyncIterator[dict]:
    """Drive the grounded-answer pipeline, yielding UI events:

      - {"t": "status", "v": ...} : a progress milestone
      - {"t": "delta",  "v": ...} : a streamed token of the current draft
      - {"t": "reset"}            : clear the current (unverified) draft
      - {"t": "final",  "v": ...} : the verified answer (or abstention)

    The verifier still gates what is committed: a draft that fails verification
    is reset rather than left on screen, and the model gets a refined-retrieval
    retry before abstaining.
    """
    kb_map = await get_kb_outline(db)

    # Mechanical steps run on the fast, deterministic lane.
    fast_llm = build_fast_llm()
    yield {"t": "status", "v": "Searching the policy library…"}
    standalone_question = await run_in_threadpool(
        condense_to_standalone_question, fast_llm, history, message
    )
    sub_questions = await run_in_threadpool(split_into_questions, fast_llm, standalone_question)

    passages, clauses = await _retrieve_and_filter(db, fast_llm, sub_questions)
    context_block = _build_context_block(passages, clauses, cross_session_context)

    yield {"t": "status", "v": "Drafting your answer…"}
    failed = False
    async for event in _stream_drafts_and_verify(
        system_prompt, history, message, standalone_question, context_block, kb_map
    ):
        if event["t"] == "_failed":
            failed = True
            continue
        yield event
        if event["t"] == "final":
            return
    if not failed:
        return

    # Agentic re-retrieval: the first context did not yield a verifiable answer,
    # so refine the query, retrieve again, merge, and try once more.
    yield {"t": "reset"}
    yield {"t": "status", "v": "Double-checking the sources…"}
    refined_query = await run_in_threadpool(
        build_refined_search_query, fast_llm, standalone_question, _found_labels(passages, clauses)
    )
    if refined_query:
        more_passages = await _retrieve_passages(refined_query, [refined_query])
        more_clauses = await expand_clauses(db, more_passages)
        more_passages, more_clauses = await _filter_applicable(
            sub_questions, more_passages, more_clauses
        )
        passages = _merge_passages(passages, more_passages)
        clauses = _merge_clauses(clauses, more_clauses)
        context_block = _build_context_block(passages, clauses, cross_session_context)

        yield {"t": "status", "v": "Drafting your answer…"}
        async for event in _stream_drafts_and_verify(
            system_prompt, history, message, standalone_question, context_block, kb_map
        ):
            if event["t"] == "_failed":
                continue
            yield event
            if event["t"] == "final":
                return

    yield {"t": "final", "v": UNSURE_RESPONSE}


async def produce_grounded_answer(
    db,
    history: list[ChatMessage],
    cross_session_context: str,
    system_prompt: str,
    message: str,
) -> str:
    """Non-streaming entry point (eval, smoke, ask). Drives the streaming
    pipeline and returns only the final verified answer."""
    final = UNSURE_RESPONSE
    async for event in stream_grounded_answer(
        db, history, cross_session_context, system_prompt, message
    ):
        if event["t"] == "final":
            final = event["v"]
    return final
