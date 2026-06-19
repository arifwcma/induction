import json
import re
import shutil
import subprocess
import tempfile
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

TOP_CLAUSE = re.compile(r"^(\d{1,2})\.\s+([A-Za-z][A-Za-z0-9 ,/'’()&\-]{2,60})\s*$")
NUMBER_ONLY = re.compile(r"^(\d{1,2})\.?$")
ALLCAPS_TITLE = re.compile(r"^[A-Z][A-Z0-9 ,/'’()&\-]{2,60}$")
SUB_CLAUSE = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){1,3})\.?\s*$")
APPENDIX = re.compile(r"^APPENDIX\s+([A-Z]):?\s*[-–]?\s*(.*)$", re.IGNORECASE)


@dataclass
class ClauseUnit:
    clause_number: str
    title: str
    parent_path: list[str]
    page: int
    text_lines: list[str] = field(default_factory=list)
    source: str = ""
    category: str = ""

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


def collect_pdf_lines(document) -> list[tuple[str, int]]:
    collected = []
    for page_index in range(document.page_count):
        page_number = page_index + 1
        for raw_line in document[page_index].get_text().splitlines():
            collected.append((raw_line, page_number))
    return collected


def next_meaningful_index(lines: list[tuple[str, int]], start: int) -> int:
    index = start
    while index < len(lines) and is_noise(lines[index][0]):
        index += 1
    return index


def merge_split_top_headings(lines: list[tuple[str, int]]) -> list[tuple[str, int]]:
    merged: list[tuple[str, int]] = []
    index = 0
    while index < len(lines):
        line, page = lines[index]
        number_match = NUMBER_ONLY.match(line.strip())
        if number_match:
            title_index = next_meaningful_index(lines, index + 1)
            if title_index < len(lines):
                candidate_title = lines[title_index][0].strip()
                if ALLCAPS_TITLE.match(candidate_title):
                    merged.append((f"{number_match.group(1)}. {candidate_title}", page))
                    index = title_index + 1
                    continue
        merged.append((line, page))
        index += 1
    return merged


def parse_pdf_clauses(pdf_path: Path) -> list[ClauseUnit]:
    document = fitz.open(pdf_path)
    units: list[ClauseUnit] = []

    current_appendix = ""
    current_appendix_key = ""
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

    lines = merge_split_top_headings(collect_pdf_lines(document))
    for raw_line, page_number in lines:
        if is_noise(raw_line):
            continue

        heading = detect_heading(raw_line)
        if heading is None:
            if current_unit is not None:
                current_unit.text_lines.append(raw_line.strip())
            continue

        kind, number_or_label, title = heading
        if kind == "appendix":
            # The appendix title repeats as a running page header on every page of
            # the appendix. Only the first occurrence opens the appendix; later
            # repeats of the same appendix are header noise and must not start a
            # new unit (otherwise the appendix is split by page instead of by clause).
            if current_appendix_key == number_or_label:
                continue
            current_appendix = f"{number_or_label}: {title}".strip(": ")
            current_appendix_key = number_or_label
            current_top_label = ""
            start_unit(number_or_label, title, page_number)
        elif kind == "top":
            if current_appendix:
                # Numbering restarts inside an appendix (1., 1.1, 1.5, ...). Treat a
                # numbered heading here as a sub-unit OF the appendix rather than a
                # new top-level clause, so the appendix stays whole and splits finely.
                start_unit(number_or_label, title, page_number)
            else:
                current_top_label = f"{number_or_label}. {title}"
                start_unit(number_or_label, title, page_number)
        else:
            start_unit(number_or_label, "", page_number)

    structured_units = [unit for unit in units if unit.body().strip()]
    if structured_units:
        document.close()
        return structured_units

    fallback_units = page_text_units(document, pdf_path.name)
    document.close()
    return fallback_units


def page_text_units(document, source: str) -> list[ClauseUnit]:
    units = []
    for page_index in range(document.page_count):
        page_number = page_index + 1
        page_lines = []
        for raw_line in document[page_index].get_text().splitlines():
            if is_noise(raw_line):
                continue
            stripped = raw_line.strip()
            if stripped:
                page_lines.append(stripped)
        if not page_lines:
            continue
        unit = ClauseUnit(
            clause_number="",
            title="",
            parent_path=[],
            page=page_number,
            source=source,
        )
        unit.text_lines = page_lines
        units.append(unit)
    return units


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


def readable_name(path: Path) -> str:
    stem = path.stem
    if stem.lower().startswith("link_"):
        stem = stem[len("link_"):]
    cleaned = stem.replace("_", " ").replace("-", " ").strip()
    return cleaned.title() if cleaned else path.name


def single_unit(source: str, title: str, lines: list[str]) -> list[ClauseUnit]:
    meaningful = [line.strip() for line in lines if line.strip()]
    if not meaningful:
        return []
    unit = ClauseUnit(clause_number="", title=title, parent_path=[], page=0, source=source)
    unit.text_lines = meaningful
    return [unit]


def flatten_json(data, indent: int = 0) -> list[str]:
    pad = "  " * indent
    lines: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{pad}{key}:")
                lines.extend(flatten_json(value, indent + 1))
            else:
                lines.append(f"{pad}{key}: {value}")
    elif isinstance(data, list):
        for item in data:
            lines.extend(flatten_json(item, indent))
    else:
        lines.append(f"{pad}{data}")
    return lines


def parse_json_document(json_path: Path) -> list[ClauseUnit]:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    return single_unit(json_path.name, readable_name(json_path), flatten_json(data))


def parse_text_document(txt_path: Path) -> list[ClauseUnit]:
    text = txt_path.read_text(encoding="utf-8", errors="ignore")
    return single_unit(txt_path.name, readable_name(txt_path), text.splitlines())


def fetch_url_text(url: str) -> str:
    try:
        import trafilatura
    except ImportError:
        print("  [skip] trafilatura is not installed; cannot read link_ files.")
        return ""
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return ""
    return trafilatura.extract(downloaded) or ""


def parse_link_document(link_path: Path) -> list[ClauseUnit]:
    url = link_path.read_text(encoding="utf-8", errors="ignore").strip()
    if not url:
        return []
    text = fetch_url_text(url)
    if not text:
        print(f"  [skip] {link_path.name}: could not extract content from {url}")
        return []
    readable = readable_name(link_path)
    return single_unit(readable, readable, text.splitlines())


def convert_doc_to_docx(doc_path: Path, out_dir: Path) -> Path | None:
    executable = shutil.which("soffice") or shutil.which("libreoffice")
    if executable is None:
        print(f"  [skip] {doc_path.name}: LibreOffice (soffice) not found; cannot read .doc files.")
        return None
    try:
        subprocess.run(
            [executable, "--headless", "--convert-to", "docx", "--outdir", str(out_dir), str(doc_path)],
            check=True,
            capture_output=True,
            timeout=180,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        print(f"  [skip] {doc_path.name}: .doc conversion failed ({error}).")
        return None
    converted = out_dir / (doc_path.stem + ".docx")
    return converted if converted.exists() else None


def parse_doc_via_conversion(doc_path: Path) -> list[ClauseUnit]:
    with tempfile.TemporaryDirectory() as temp_dir:
        converted = convert_doc_to_docx(doc_path, Path(temp_dir))
        if converted is None:
            return []
        units = parse_docx_sections(converted)
    for unit in units:
        unit.source = doc_path.name
    return units


def parse_document(path: Path) -> list[ClauseUnit]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return parse_pdf_clauses(path)
    if suffix == ".docx":
        return parse_docx_sections(path)
    if suffix == ".doc":
        return parse_doc_via_conversion(path)
    if suffix == ".json":
        return parse_json_document(path)
    if suffix == ".txt":
        if path.name.lower().startswith("link_"):
            return parse_link_document(path)
        return parse_text_document(path)
    return []


if __name__ == "__main__":
    documents_dir = Path("documents")
    for document_path in sorted(documents_dir.rglob("*.*")):
        if document_path.name.startswith("~$") or document_path.name == "objectives.json":
            continue
        parsed_units = parse_document(document_path)
        print(f"{document_path.name}: {len(parsed_units)} units")
        for unit in parsed_units[:3]:
            print(f"  [{unit.page}] {unit.breadcrumb()} :: {unit.body()[:80]!r}")
