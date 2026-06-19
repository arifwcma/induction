from io import BytesIO

import fitz
from docx import Document as DocxFile
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter

from app.kb.contextual import CHUNK_OVERLAP, CHUNK_SIZE
from app.rag.engine import get_vector_store
from app.rag.retrieval import get_index


def read_pdf_bytes(data: bytes) -> str:
    pdf = fitz.open(stream=data, filetype="pdf")
    page_texts = []
    for page_index in range(pdf.page_count):
        page_text = pdf[page_index].get_text().strip()
        if page_text:
            page_texts.append(page_text)
    pdf.close()
    return "\n".join(page_texts)


def read_docx_bytes(data: bytes) -> str:
    docx_file = DocxFile(BytesIO(data))
    lines = [paragraph.text.strip() for paragraph in docx_file.paragraphs if paragraph.text.strip()]
    return "\n".join(lines)


def extract_text_from_upload(filename: str, data: bytes) -> str:
    lowered_name = filename.lower()
    if lowered_name.endswith(".pdf"):
        return read_pdf_bytes(data)
    if lowered_name.endswith(".docx"):
        return read_docx_bytes(data)
    if lowered_name.endswith(".txt"):
        return data.decode("utf-8", errors="ignore").strip()
    raise ValueError("Unsupported file type. Upload a PDF, DOCX, or TXT file.")


def add_text_to_knowledge_base(text: str, source_label: str, trainer_name: str, kb_entry_id: str):
    splitter = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    header = "[Knowledge added by management for induction]\nScope: general provision."
    index = get_index()
    for piece in splitter.split_text(text):
        document = Document(
            text=f"{header}\n\n{piece}",
            metadata={
                "source": source_label,
                "origin": "trainer",
                "trainer": trainer_name,
                "scope": "general",
                "condition": "",
                "clause_number": "",
                "raw_text": piece,
                "kb_entry_id": kb_entry_id,
            },
        )
        document.id_ = kb_entry_id
        index.insert(document)


def remove_from_knowledge_base(kb_entry_id: str):
    get_vector_store().delete(ref_doc_id=kb_entry_id)
