import asyncio
from pathlib import Path

from llama_index.core import Document, StorageContext, VectorStoreIndex
from sqlalchemy import delete

from app.config import get_settings
from app.db import async_session_maker, create_db_and_tables
from app.kb.bm25_index import save_corpus
from app.kb.clause_model import build_clause_record
from app.kb.contextual import situate_and_chunk
from app.kb.parse import parse_document
from app.models import Clause
from app.rag.engine import configure_models, get_vector_store


def list_document_paths() -> list[Path]:
    documents_dir = Path(get_settings().documents_dir)
    paths = []
    for path in sorted(documents_dir.glob("*.*")):
        if path.name.startswith("~$"):
            continue
        if path.suffix.lower() in (".pdf", ".docx"):
            paths.append(path)
    return paths


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

    for document_path in list_document_paths():
        units = parse_document(document_path)
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
