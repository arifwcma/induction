from pathlib import Path

import fitz
from llama_index.core import Document, StorageContext, VectorStoreIndex

from app.config import get_settings
from app.rag.engine import configure_models, get_vector_store


def load_pdf_pages() -> list[Document]:
    settings = get_settings()
    documents_dir = Path(settings.documents_dir)

    pages = []
    for pdf_path in sorted(documents_dir.glob("*.pdf")):
        pdf = fitz.open(pdf_path)
        for page_index in range(pdf.page_count):
            page_text = pdf[page_index].get_text().strip()
            if not page_text:
                continue
            pages.append(
                Document(
                    text=page_text,
                    metadata={"source": pdf_path.name, "page": page_index + 1},
                )
            )
        pdf.close()
    return pages


def clear_existing_collection():
    settings = get_settings()
    vector_store = get_vector_store()
    client = vector_store.client
    if client.collection_exists(settings.qdrant_collection):
        client.delete_collection(settings.qdrant_collection)


def ingest_documents():
    configure_models()
    settings = get_settings()

    clear_existing_collection()

    pages = load_pdf_pages()
    vector_store = get_vector_store()
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    VectorStoreIndex.from_documents(pages, storage_context=storage_context)

    print(f"Ingested {len(pages)} pages into collection '{settings.qdrant_collection}'.")


if __name__ == "__main__":
    ingest_documents()
