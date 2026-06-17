from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SystemPromptConfig


PROMPT_ROW_ID = 1


async def ensure_prompt_seeded(db: AsyncSession, default_prompt: str):
    existing = await db.get(SystemPromptConfig, PROMPT_ROW_ID)
    if existing is None:
        db.add(SystemPromptConfig(id=PROMPT_ROW_ID, prompt=default_prompt))
        await db.commit()


async def get_system_prompt(db: AsyncSession, default_prompt: str) -> str:
    config_row = await db.get(SystemPromptConfig, PROMPT_ROW_ID)
    if config_row is None:
        return default_prompt
    return config_row.prompt


async def update_system_prompt(db: AsyncSession, new_prompt: str):
    config_row = await db.get(SystemPromptConfig, PROMPT_ROW_ID)
    if config_row is None:
        db.add(SystemPromptConfig(id=PROMPT_ROW_ID, prompt=new_prompt))
    else:
        config_row.prompt = new_prompt
    await db.commit()
