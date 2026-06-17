import sys

from app.rag.chat import (
    DEFAULT_SYSTEM_PROMPT,
    UNSURE_RESPONSE,
    format_context,
    generate_answer,
    verify_answer,
)
from app.rag.retrieval import retrieve_relevant_passages, top_passage_is_confident


def ask_cli():
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        print('Usage: python -m app.ask "your question"')
        return

    passages = retrieve_relevant_passages(question)
    if not top_passage_is_confident(passages):
        print(UNSURE_RESPONSE)
        return

    context_block = format_context(passages, [])
    answer = generate_answer(DEFAULT_SYSTEM_PROMPT, [], context_block, question)
    verdict = verify_answer(context_block, question, answer)
    if not verdict.passed:
        print(UNSURE_RESPONSE)
        return
    print(answer)


if __name__ == "__main__":
    ask_cli()
