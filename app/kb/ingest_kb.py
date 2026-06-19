import asyncio
from pathlib import Path

from llama_index.core import Document, StorageContext, VectorStoreIndex
from sqlalchemy import delete

from app.config import get_settings
from app.db import async_session_maker, create_db_and_tables
from app.kb.bm25_index import save_corpus
from app.kb.categories import load_category_objectives
from app.kb.clause_model import build_clause_record
from app.kb.contextual import situate_and_chunk
from app.kb.parse import parse_document
from app.models import Clause
from app.rag.engine import configure_models, get_vector_store


SUPPORTED_SUFFIXES = (".pdf", ".docx", ".doc", ".json", ".txt")


def list_categorised_documents() -> list[tuple[Path, str]]:
    """Return (path, category) for every ingestible document.

    Only the folders named in objectives.json count as induction categories,
    so a holding folder or stray root file is never ingested. The walk is
    recursive within each category folder."""
    documents_dir = Path(get_settings().documents_dir)
    objectives = load_category_objectives()

    discovered: list[tuple[Path, str]] = []
    for category in objectives:
        category_dir = documents_dir / category
        if not category_dir.is_dir():
            print(f"  [skip] category '{category}' has no folder at {category_dir}")
            continue
        for path in sorted(category_dir.rglob("*.*")):
            if path.name.startswith("~$"):
                continue
            if path.suffix.lower() in SUPPORTED_SUFFIXES:
                discovered.append((path, category))
    return discovered


def clear_vector_collection():
    settings = get_settings()
    client = get_vector_store().client
    if client.collection_exists(settings.qdrant_collection):
        client.delete_collection(settings.qdrant_collection)


async def persist_clause_records(clause_records: list[dict]):
    await create_db_and_tables()
    async with async_session_maker() as db:
        await db.execute(delete(Clause))
        for record in clause_records:
            db.add(Clause(**record))
        await db.commit()


def ingest_knowledge_base():
    configure_models()
    clear_vector_collection()

    documents_for_embedding = []
    bm25_records = []
    clause_records = []

    for document_path, category in list_categorised_documents():
        units = parse_document(document_path)
        for unit in units:
            unit.category = category
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

    storage_context = StorageContext.from_defaults(vector_store=get_vector_store())
    VectorStoreIndex.from_documents(documents_for_embedding, storage_context=storage_context)

    save_corpus(bm25_records)
    asyncio.run(persist_clause_records(clause_records))

    print(
        f"Ingested {len(documents_for_embedding)} contextual chunks, "
        f"{len(clause_records)} clauses, {len(bm25_records)} BM25 records."
    )


if __name__ == "__main__":
    ingest_knowledge_base()
