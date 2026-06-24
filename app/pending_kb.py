"""Trainer-contributed knowledge that is staged on disk and ingested on demand.

The trainer "Add to KB" note and the "Upload document to KB" file are NOT
ingested instantly. Each is written to the writable ``documents/trainer`` volume
and recorded as a PendingIngest row. When a trainer clicks "Apply pending", every
pending file is embedded + indexed in-process (via the ingest_one core) and the
BM25 / KB-map caches are refreshed, so the new knowledge becomes retrievable
without restarting the container (which it cannot do anyway: cap_drop ALL, no
docker socket).

Putting the files under a ``trainer`` category that is listed in objectives.json
also means a future full re-ingest re-walks them, so applied trainer knowledge
survives a destructive rebuild.
"""

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.config import get_settings
from app.ingest_one import embed_and_index_file
from app.models import (
    PENDING_STATUS_APPLIED,
    PENDING_STATUS_PENDING,
    Clause,
    PendingIngest,
)
from app.rag.kb_outline import reset_outline_cache
from app.rag.retrieval import reset_bm25_cache


TRAINER_CATEGORY = "trainer"
TRAINER_ORIGIN = "trainer"
SUPPORTED_UPLOAD_SUFFIXES = {".pdf", ".docx", ".txt"}


def trainer_dir() -> Path:
    path = Path(get_settings().documents_dir) / TRAINER_CATEGORY
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_slug(text: str, max_length: int = 40) -> str:
    lowered = text.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    slug = slug[:max_length].strip("-")
    return slug or "note"


def unique_filename(stem: str, suffix: str) -> str:
    return f"{safe_slug(stem)}-{uuid.uuid4().hex[:8]}{suffix}"


def write_trainer_text(text: str) -> str:
    filename = unique_filename(text, ".txt")
    (trainer_dir() / filename).write_text(text, encoding="utf-8")
    return filename


def write_trainer_upload(original_filename: str, data: bytes) -> str:
    suffix = Path(original_filename).suffix.lower()
    if suffix not in SUPPORTED_UPLOAD_SUFFIXES:
        raise ValueError("Unsupported file type. Upload a PDF, DOCX, or TXT file.")
    filename = unique_filename(Path(original_filename).stem, suffix)
    (trainer_dir() / filename).write_bytes(data)
    return filename


async def create_pending(
    db: AsyncSession,
    trainer_id: uuid.UUID,
    trainer_name: str,
    kind: str,
    source_label: str,
    filename: str,
) -> PendingIngest:
    entry = PendingIngest(
        trainer_id=trainer_id,
        trainer_name=trainer_name,
        kind=kind,
        source_label=source_label,
        filename=filename,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def list_pending(db: AsyncSession, status: str = PENDING_STATUS_PENDING) -> list[PendingIngest]:
    query = (
        select(PendingIngest)
        .where(PendingIngest.status == status)
        .order_by(PendingIngest.created_at)
    )
    return list((await db.execute(query)).scalars().all())


async def count_pending(db: AsyncSession) -> int:
    query = select(func.count()).select_from(PendingIngest).where(
        PendingIngest.status == PENDING_STATUS_PENDING
    )
    return int((await db.execute(query)).scalar_one())


async def apply_pending_ingests(db: AsyncSession) -> int:
    """Ingest every pending trainer file and mark it applied; refresh caches.

    The embedding/indexing for each file runs in a worker thread (it makes
    blocking LLM/embedding calls and must not touch the async DB), then the
    returned clause records are persisted on this event loop's session. Already
    applied rows are skipped, so re-clicking Apply never duplicates content."""
    rows = await list_pending(db, PENDING_STATUS_PENDING)
    directory = trainer_dir()
    applied = 0

    for row in rows:
        path = directory / row.filename
        if path.exists():
            clause_records = await run_in_threadpool(
                embed_and_index_file, path, TRAINER_CATEGORY, TRAINER_ORIGIN
            )
            for record in clause_records:
                db.add(Clause(**record))
            applied += 1
        row.status = PENDING_STATUS_APPLIED
        row.applied_at = datetime.now(timezone.utc)
        await db.commit()

    if applied:
        reset_bm25_cache()
        reset_outline_cache()
    return applied
