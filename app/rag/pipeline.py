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
    generate_answer,
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
    # De-duplicate while preserving order.
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


async def _draft_and_verify(
    system_prompt: str,
    history: list[ChatMessage],
    message: str,
    standalone_question: str,
    context_block: str,
    kb_map: str,
) -> str | None:
    """Generate (answer lane) and verify (fast lane). Vary the draft across
    attempts so a transient verifier rejection can recover. Returns the answer on
    a passing verdict, otherwise None."""
    for attempt in range(DRAFT_ATTEMPTS):
        answer = await run_in_threadpool(
            generate_answer, system_prompt, history, context_block, message, kb_map, attempt
        )
        verdict = await run_in_threadpool(
            verify_answer, context_block, standalone_question, answer, kb_map
        )
        if verdict.passed:
            return answer
    return None


async def _retrieve_and_filter(
    db, applicability_question: str, rerank_query: str, extra_queries: list[str]
):
    passages = await run_in_threadpool(retrieve_relevant_passages, rerank_query, extra_queries)
    clauses = await expand_clauses(db, passages)
    passages, clauses = await run_in_threadpool(
        keep_applicable, applicability_question, passages, clauses
    )
    return passages, clauses


async def produce_grounded_answer(
    db,
    history: list[ChatMessage],
    cross_session_context: str,
    system_prompt: str,
    message: str,
) -> str:
    kb_map = await get_kb_outline(db)

    # Mechanical steps run on the fast, deterministic lane.
    fast_llm = build_fast_llm()
    standalone_question = await run_in_threadpool(
        condense_to_standalone_question, fast_llm, history, message
    )
    search_query = await run_in_threadpool(build_search_query, fast_llm, standalone_question)

    passages, clauses = await _retrieve_and_filter(
        db, standalone_question, standalone_question, [search_query]
    )
    context_block = _build_context_block(passages, clauses, cross_session_context)

    answer = await _draft_and_verify(
        system_prompt, history, message, standalone_question, context_block, kb_map
    )
    if answer is not None:
        return answer

    # Agentic re-retrieval: the first context did not yield a verifiable answer, so
    # ask the fast model for a different, concept-focused query informed by what we
    # already found, retrieve again, merge, and try once more. This rescues hard or
    # awkwardly-worded questions instead of abstaining prematurely.
    refined_query = await run_in_threadpool(
        build_refined_search_query, fast_llm, standalone_question, _found_labels(passages, clauses)
    )
    if refined_query:
        more_passages, more_clauses = await _retrieve_and_filter(
            db, standalone_question, refined_query, [search_query, standalone_question]
        )
        passages = _merge_passages(passages, more_passages)
        clauses = _merge_clauses(clauses, more_clauses)
        context_block = _build_context_block(passages, clauses, cross_session_context)

        answer = await _draft_and_verify(
            system_prompt, history, message, standalone_question, context_block, kb_map
        )
        if answer is not None:
            return answer

    return UNSURE_RESPONSE
