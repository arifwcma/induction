from dataclasses import dataclass

from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI

from app.config import get_settings
from app.kb.parse import ClauseUnit


CHUNK_SIZE = 700
CHUNK_OVERLAP = 150

SITUATING_PROMPT = (
    "You are preparing a passage from an organisational document for retrieval. "
    "Write 2-3 sentences (under 100 tokens) that situate this passage within the document so it "
    "can be understood on its own. You MUST state any condition that limits when the passage "
    "applies (for example: applies only during an emergency / AIIMS activation, only to casual "
    "employees, only during probation, only to a specific band). If the passage states a general "
    "rule with no such limit, say it is a general provision. Do not add facts that are not present.\n"
    "After the sentences, add two final lines in exactly this form:\n"
    "TITLE: <a short 2-6 word topic heading for this passage>\n"
    "SCOPE: general\n"
    "or\n"
    "SCOPE: conditional - <the condition in a few words>\n\n"
    "Document: {document}\n"
    "Location: {breadcrumb}\n"
    "Passage:\n{body}\n\n"
    "Situating context:"
)


@dataclass
class SituatingResult:
    prose: str
    scope: str
    condition: str
    title: str = ""


@dataclass
class ContextualChunk:
    text_for_index: str
    raw_text: str
    metadata: dict


def build_situating_llm() -> OpenAI:
    settings = get_settings()
    return OpenAI(model=settings.openai_chat_model, api_key=settings.openai_api_key, max_tokens=180)


def parse_situating_output(output: str) -> SituatingResult:
    prose_lines = []
    scope = "general"
    condition = ""
    title = ""
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("TITLE:"):
            title = stripped[len("TITLE:"):].strip()
        elif stripped.upper().startswith("SCOPE:"):
            value = stripped[len("SCOPE:"):].strip()
            if value.lower().startswith("conditional"):
                scope = "conditional"
                remainder = value[len("conditional"):].lstrip(" -:").strip()
                condition = remainder
            else:
                scope = "general"
        elif stripped:
            prose_lines.append(stripped)
    return SituatingResult(
        prose=" ".join(prose_lines).strip(), scope=scope, condition=condition, title=title
    )


def situate_unit(llm: OpenAI, unit: ClauseUnit) -> SituatingResult:
    prompt = SITUATING_PROMPT.format(
        document=unit.source,
        breadcrumb=unit.breadcrumb(),
        body=unit.body()[:2000],
    )
    return parse_situating_output(llm.complete(prompt).text.strip())


def effective_title(unit: ClauseUnit, situating: SituatingResult) -> str:
    if unit.title.strip():
        return unit.title.strip()
    return situating.title.strip()


def effective_breadcrumb(unit: ClauseUnit, situating: SituatingResult) -> str:
    title = effective_title(unit, situating)
    heading_parts = [part for part in [unit.clause_number, title] if part]
    heading_label = " ".join(heading_parts)
    trail = unit.parent_path + [heading_label]
    return " > ".join(part for part in trail if part)


def split_body(body: str) -> list[str]:
    splitter = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    return splitter.split_text(body)


def context_header(unit: ClauseUnit, situating: SituatingResult) -> str:
    scope_line = "Scope: general provision."
    if situating.scope == "conditional":
        scope_line = f"Scope: conditional - applies only when {situating.condition}."
    return (
        f"[{unit.source}] {effective_breadcrumb(unit, situating)}\n"
        f"Context: {situating.prose}\n"
        f"{scope_line}"
    )


def chunks_for_unit(unit: ClauseUnit, situating: SituatingResult) -> list[ContextualChunk]:
    breadcrumb = effective_breadcrumb(unit, situating)
    title = effective_title(unit, situating)
    header = context_header(unit, situating)
    chunks = []
    for piece in split_body(unit.body()):
        chunks.append(
            ContextualChunk(
                text_for_index=f"{header}\n\n{piece}",
                raw_text=piece,
                metadata={
                    "source": unit.source,
                    "clause_number": unit.clause_number,
                    "title": title,
                    "breadcrumb": breadcrumb,
                    "situating_context": situating.prose,
                    "scope": situating.scope,
                    "condition": situating.condition,
                    "page": unit.page,
                },
            )
        )
    return chunks


def situate_and_chunk(units: list[ClauseUnit]):
    llm = build_situating_llm()
    for unit in units:
        situating = situate_unit(llm, unit)
        yield unit, situating, chunks_for_unit(unit, situating)


def build_contextual_chunks(units: list[ClauseUnit]) -> list[ContextualChunk]:
    chunks: list[ContextualChunk] = []
    for _unit, _situating, unit_chunks in situate_and_chunk(units):
        chunks.extend(unit_chunks)
    return chunks


if __name__ == "__main__":
    from pathlib import Path

    from app.kb.parse import parse_document

    units = parse_document(Path("documents/Wimmera CMA Enterprise Agreement 2024-2028.pdf"))
    sample = [unit for unit in units if unit.clause_number in ("23.3",) or "Appendix C" in unit.breadcrumb()][:2]
    for chunk in build_contextual_chunks(sample):
        print("----")
        print("scope:", chunk.metadata["scope"], "| condition:", chunk.metadata["condition"])
        print(chunk.text_for_index[:400])
