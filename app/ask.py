import asyncio
import sys

from app.db import async_session_maker
from app.rag.chat import DEFAULT_SYSTEM_PROMPT
from app.rag.pipeline import produce_grounded_answer


async def answer_question(question: str) -> str:
    async with async_session_maker() as db:
        return await produce_grounded_answer(db, [], "", DEFAULT_SYSTEM_PROMPT, question)


def ask_cli():
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        print('Usage: python -m app.ask "your question"')
        return
    print(asyncio.run(answer_question(question)))


if __name__ == "__main__":
    ask_cli()
