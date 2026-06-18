from llama_index.core.llms import ChatMessage

from starlette.concurrency import run_in_threadpool

from app.rag.chat import (
    UNSURE_RESPONSE,
    build_llm,
    build_search_query,
    condense_to_standalone_question,
    format_context,
    generate_answer,
    verify_answer,
)
from app.rag.applicability import keep_applicable
from app.rag.expansion import expand_clauses
from app.rag.kb_outline import get_kb_outline
from app.rag.retrieval import retrieve_relevant_passages


async def produce_grounded_answer(
    db,
    history: list[ChatMessage],
    cross_session_context: str,
    system_prompt: str,
    message: str,
) -> str:
    kb_map = await get_kb_outline(db)
    standalone_question = await run_in_threadpool(
        condense_to_standalone_question, build_llm(), history, message
    )
    search_query = await run_in_threadpool(build_search_query, build_llm(), standalone_question)
    passages = await run_in_threadpool(
        retrieve_relevant_passages, standalone_question, [search_query]
    )

    clauses = await expand_clauses(db, passages)
    passages, clauses = await run_in_threadpool(
        keep_applicable, standalone_question, passages, clauses
    )
    context_block = format_context(passages, clauses)
    if cross_session_context:
        context_block = f"{context_block}\n\n[Background from earlier sessions]\n{cross_session_context}"

    for _attempt in range(2):
        answer = await run_in_threadpool(
            generate_answer, system_prompt, history, context_block, message, kb_map
        )
        verdict = await run_in_threadpool(
            verify_answer, context_block, standalone_question, answer, kb_map
        )
        if verdict.passed:
            return answer

    return UNSURE_RESPONSE
