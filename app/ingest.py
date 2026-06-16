from pathlib import Path

import fitz
from docx import Document as DocxFile
from llama_index.core import Document, StorageContext, VectorStoreIndex

from app.config import get_settings
from app.rag.engine import configure_models, get_vector_store


def load_pdf_pages(documents_dir: Path) -> list[Document]:
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


def read_docx_text(docx_path: Path) -> str:
    docx_file = DocxFile(docx_path)

    lines = []
    for paragraph in docx_file.paragraphs:
        paragraph_text = paragraph.text.strip()
        if paragraph_text:
            lines.append(paragraph_text)

    for table in docx_file.tables:
        for row in table.rows:
            filled_cells = []
            for cell in row.cells:
                cell_text = cell.text.strip()
                if cell_text:
                    filled_cells.append(cell_text)
            if filled_cells:
                lines.append(" | ".join(filled_cells))

    return "\n".join(lines)


def load_docx_documents(documents_dir: Path) -> list[Document]:
    documents = []
    for docx_path in sorted(documents_dir.glob("*.docx")):
        if docx_path.name.startswith("~$"):
            continue
        full_text = read_docx_text(docx_path)
        if not full_text:
            continue
        documents.append(
            Document(
                text=full_text,
                metadata={"source": docx_path.name},
            )
        )
    return documents


def clear_existing_collection():
    settings = get_settings()
    vector_store = get_vector_store()
    client = vector_store.client
    if client.collection_exists(settings.qdrant_collection):
        client.delete_collection(settings.qdrant_collection)


def ingest_documents():
    configure_models()
    settings = get_settings()
    documents_dir = Path(settings.documents_dir)

    clear_existing_collection()

    pdf_pages = load_pdf_pages(documents_dir)
    docx_documents = load_docx_documents(documents_dir)
    all_documents = pdf_pages + docx_documents

    vector_store = get_vector_store()
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    VectorStoreIndex.from_documents(all_documents, storage_context=storage_context)

    print(
        f"Ingested {len(pdf_pages)} PDF pages and {len(docx_documents)} DOCX files "
        f"into collection '{settings.qdrant_collection}'."
    )


if __name__ == "__main__":
    ingest_documents()
