"""Append a single document to the existing knowledge base (no full re-ingest).

Unlike app.kb.ingest_kb (which wipes and rebuilds every store), this script
ADDS one document to the live Qdrant collection, BM25 corpus, and clause table.
Use it to top up the KB with a new file without paying for a full rebuild.

    python -m app.ingest_one "documents/category3/Some Policy.docx" [category]

The category defaults to the document's top-level folder under documents/.
Restart the backend afterwards so the cached BM25 index and KB map reload.
"""

import asyncio
import json
import sys
from pathlib import Path

from llama_index.core import Document, StorageContext, VectorStoreIndex

from app.config import get_settings
from app.db import async_session_maker, create_db_and_tables
from app.kb.bm25_index import BM25_CORPUS_PATH
from app.kb.clause_model import build_clause_record
from app.kb.contextual import situate_and_chunk
from app.kb.parse import parse_document
from app.models import Clause
from app.rag.engine import configure_models, get_vector_store


def resolve_category(path: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    documents_dir = Path(get_settings().documents_dir).resolve()
    try:
        return path.resolve().relative_to(documents_dir).parts[0]
    except (ValueError, IndexError):
        return path.parent.name


def append_bm25_records(records: list[dict]):
    existing: list[dict] = []
    if BM25_CORPUS_PATH.exists():
        existing = json.loads(BM25_CORPUS_PATH.read_text(encoding="utf-8"))
    existing.extend(records)
    BM25_CORPUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    BM25_CORPUS_PATH.write_text(json.dumps(existing), encoding="utf-8")


async def persist_clause_records(clause_records: list[dict]):
    await create_db_and_tables()
    async with async_session_maker() as db:
        for record in clause_records:
            db.add(Clause(**record))
        await db.commit()


def embed_and_index_file(path: Path, category: str, origin: str = "") -> list[dict]:
    """Append one document to Qdrant + the BM25 corpus and return its clause records.

    This does the embedding/indexing work (the parts safe to run inside a thread,
    with no async DB access) and hands the clause records back to the caller to
    persist. The CLI wrapper persists them via asyncio.run; the in-app "apply
    pending" path persists them on the running event loop instead.
    """
    configure_models()

    units = parse_document(path)
    for unit in units:
        unit.category = category
        unit.origin = origin

    documents_for_embedding = []
    bm25_records = []
    clause_records = []

    for unit, situating, chunks in situate_and_chunk(units):
        clause_records.append(build_clause_record(unit, situating))
        for chunk in chunks:
            documents_for_embedding.append(
                Document(text=chunk.text_for_index, metadata={**chunk.metadata, "raw_text": chunk.raw_text})
            )
            bm25_records.append(
                {
                    "text_for_index": chunk.text_for_index,
                    "raw_text": chunk.raw_text,
                    "metadata": chunk.metadata,
                }
            )

    if not documents_for_embedding:
        return []

    storage_context = StorageContext.from_defaults(vector_store=get_vector_store())
    VectorStoreIndex.from_documents(documents_for_embedding, storage_context=storage_context)

    append_bm25_records(bm25_records)
    return clause_records


def ingest_one(path: Path, category: str):
    clause_records = embed_and_index_file(path, category)
    if not clause_records:
        print(f"No ingestible content found in {path.name}; nothing added.")
        return

    asyncio.run(persist_clause_records(clause_records))

    print(
        f"Appended {len(clause_records)} clauses from '{path.name}' (category={category})."
    )
    print("Restart the backend so the cached BM25 index and KB map reload.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.ingest_one <path-to-document> [category]")
        sys.exit(1)

    target = Path(sys.argv[1])
    if not target.exists():
        print(f"File not found: {target}")
        sys.exit(1)

    explicit_category = sys.argv[2] if len(sys.argv) > 2 else None
    ingest_one(target, resolve_category(target, explicit_category))
