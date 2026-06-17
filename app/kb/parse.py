import re
from dataclasses import dataclass, field
from pathlib import Path

import fitz
from docx import Document as DocxFile


NOISE_PATTERNS = [
    re.compile(r"^\s*OFFICIAL\s*$", re.IGNORECASE),
    re.compile(r"^\s*Wimmera CMA Enterprise Agreement", re.IGNORECASE),
    re.compile(r"^\s*WCMA Enterprise Agreement .*FINAL\.docx", re.IGNORECASE),
    re.compile(r"^\s*\d+\s+of\s+\d+\s*$"),
    re.compile(r"^\s*$"),
]

TOP_CLAUSE = re.compile(r"^(\d{1,2})\.\s+([A-Z][A-Z0-9 ,/'’()\-]{2,})\s*$")
SUB_CLAUSE = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){1,3})\s*$")
APPENDIX = re.compile(r"^APPENDIX\s+([A-Z]):?\s*[-–]?\s*(.*)$", re.IGNORECASE)


@dataclass
class ClauseUnit:
    clause_number: str
    title: str
    parent_path: list[str]
    page: int
    text_lines: list[str] = field(default_factory=list)
    source: str = ""

    def breadcrumb(self) -> str:
        trail = self.parent_path + [self.heading_label()]
        return " > ".join(part for part in trail if part)

    def heading_label(self) -> str:
        if self.title:
            return f"{self.clause_number} {self.title}".strip()
        return self.clause_number

    def body(self) -> str:
        return "\n".join(line for line in self.text_lines if line.strip())


def is_noise(line: str) -> bool:
    for pattern in NOISE_PATTERNS:
        if pattern.match(line):
            return True
    return False


TOC_LEADER = re.compile(r"\.{4,}")


def detect_heading(line: str):
    if TOC_LEADER.search(line):
        return None

    appendix_match = APPENDIX.match(line.strip())
    if appendix_match:
        letter = appendix_match.group(1).upper()
        title = appendix_match.group(2).strip(" -–:")
        return ("appendix", f"Appendix {letter}", title)

    top_match = TOP_CLAUSE.match(line.strip())
    if top_match:
        return ("top", top_match.group(1), top_match.group(2).strip())

    sub_match = SUB_CLAUSE.match(line.strip())
    if sub_match:
        return ("sub", sub_match.group(1), "")

    return None


def parse_pdf_clauses(pdf_path: Path) -> list[ClauseUnit]:
    document = fitz.open(pdf_path)
    units: list[ClauseUnit] = []

    current_appendix = ""
    current_top_label = ""
    current_unit: ClauseUnit | None = None

    def start_unit(clause_number: str, title: str, page: int):
        nonlocal current_unit
        parent_path = []
        if current_appendix:
            parent_path.append(current_appendix)
        elif current_top_label:
            parent_path.append(current_top_label)
        current_unit = ClauseUnit(
            clause_number=clause_number,
            title=title,
            parent_path=parent_path,
            page=page,
            source=pdf_path.name,
        )
        units.append(current_unit)

    for page_index in range(document.page_count):
        page_number = page_index + 1
        for raw_line in document[page_index].get_text().splitlines():
            if is_noise(raw_line):
                continue

            heading = detect_heading(raw_line)
            if heading is None:
                if current_unit is not None:
                    current_unit.text_lines.append(raw_line.strip())
                continue

            kind, number_or_label, title = heading
            if kind == "appendix":
                current_appendix = f"{number_or_label}: {title}".strip(": ")
                current_top_label = ""
                start_unit(number_or_label, title, page_number)
            elif kind == "top":
                current_appendix = ""
                current_top_label = f"{number_or_label}. {title}"
                start_unit(number_or_label, title, page_number)
            else:
                start_unit(number_or_label, "", page_number)

    document.close()
    return [unit for unit in units if unit.body().strip()]


def is_docx_heading(paragraph) -> bool:
    style_name = getattr(paragraph.style, "name", "") or ""
    return style_name.startswith("Heading") or style_name == "Title"


def parse_docx_sections(docx_path: Path) -> list[ClauseUnit]:
    docx_file = DocxFile(docx_path)
    units: list[ClauseUnit] = []
    current_unit: ClauseUnit | None = None

    for paragraph in docx_file.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        if is_docx_heading(paragraph):
            current_unit = ClauseUnit(
                clause_number="",
                title=text,
                parent_path=[],
                page=0,
                source=docx_path.name,
            )
            units.append(current_unit)
        elif current_unit is not None:
            current_unit.text_lines.append(text)
        else:
            current_unit = ClauseUnit(
                clause_number="",
                title="Introduction",
                parent_path=[],
                page=0,
                source=docx_path.name,
            )
            units.append(current_unit)
            current_unit.text_lines.append(text)

    table_lines = []
    for table in docx_file.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                table_lines.append(" | ".join(cells))
    if table_lines:
        table_unit = ClauseUnit(
            clause_number="",
            title="Tables",
            parent_path=[],
            page=0,
            source=docx_path.name,
        )
        table_unit.text_lines = table_lines
        units.append(table_unit)

    return [unit for unit in units if unit.body().strip()]


def parse_document(path: Path) -> list[ClauseUnit]:
    if path.suffix.lower() == ".pdf":
        return parse_pdf_clauses(path)
    if path.suffix.lower() == ".docx":
        return parse_docx_sections(path)
    return []


if __name__ == "__main__":
    documents_dir = Path("documents")
    for document_path in sorted(documents_dir.glob("*.*")):
        if document_path.name.startswith("~$"):
            continue
        parsed_units = parse_document(document_path)
        print(f"{document_path.name}: {len(parsed_units)} units")
        for unit in parsed_units[:3]:
            print(f"  [{unit.page}] {unit.breadcrumb()} :: {unit.body()[:80]!r}")
