import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TrainerKBEntry


async def create_kb_entry(
    db: AsyncSession,
    trainer_id: uuid.UUID,
    trainer_name: str,
    kind: str,
    source_label: str,
    content: str,
    filename: str = "",
) -> TrainerKBEntry:
    entry = TrainerKBEntry(
        trainer_id=trainer_id,
        trainer_name=trainer_name,
        kind=kind,
        source_label=source_label,
        content=content,
        filename=filename,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def list_kb_entries(db: AsyncSession) -> list[TrainerKBEntry]:
    query = select(TrainerKBEntry).order_by(TrainerKBEntry.created_at.desc())
    return list((await db.execute(query)).scalars().all())


async def get_kb_entry(db: AsyncSession, entry_id: uuid.UUID) -> TrainerKBEntry | None:
    return await db.get(TrainerKBEntry, entry_id)


async def delete_kb_entry(db: AsyncSession, entry: TrainerKBEntry):
    await db.delete(entry)
    await db.commit()
