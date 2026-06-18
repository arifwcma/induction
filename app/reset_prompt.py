import asyncio

from app.config_store import update_system_prompt
from app.db import async_session_maker, create_db_and_tables
from app.rag.chat import DEFAULT_SYSTEM_PROMPT


async def reset_prompt():
    await create_db_and_tables()
    async with async_session_maker() as db:
        await update_system_prompt(db, DEFAULT_SYSTEM_PROMPT)
    print(f"System prompt reset to current default ({len(DEFAULT_SYSTEM_PROMPT)} chars).")


if __name__ == "__main__":
    asyncio.run(reset_prompt())
