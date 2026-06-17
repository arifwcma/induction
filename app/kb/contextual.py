from dataclasses import dataclass

from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI

from app.config import get_settings
from app.kb.parse import ClauseUnit


CHUNK_SIZE = 700
CHUNK_OVERLAP = 150
SITUATING_TOKEN_BUDGET = 100

SITUATING_PROMPT = (
    "You are preparing a passage from an organisational document for retrieval. "
    "Write 2-3 sentences (under 100 tokens) that situate this passage within the document so it "
    "can be understood on its own. You MUST state any condition that limits when the passage "
    "applies (for example: applies only during an emergency / AIIMS activation, only to casual "
    "employees, only during probation, only to a specific band). If the passage states a general "
    "rule with no such limit, say it is a general provision. Do not add facts that are not present.\n\n"
    "Document: {document}\n"
    "Location: {breadcrumb}\n"
    "Passage:\n{body}\n\n"
    "Situating context:"
)


@dataclass
class ContextualChunk:
    text_for_index: str
    raw_text: str
    metadata: dict


def build_situating_llm() -> OpenAI:
    settings = get_settings()
    return OpenAI(model=settings.openai_chat_model, api_key=settings.openai_api_key, max_tokens=160)


def situate_unit(llm: OpenAI, unit: ClauseUnit) -> str:
    prompt = SITUATING_PROMPT.format(
        document=unit.source,
        breadcrumb=unit.breadcrumb(),
        body=unit.body()[:2000],
    )
    return llm.complete(prompt).text.strip()


def split_body(body: str) -> list[str]:
    splitter = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    return splitter.split_text(body)


def build_contextual_chunks(units: list[ClauseUnit]) -> list[ContextualChunk]:
    llm = build_situating_llm()
    chunks: list[ContextualChunk] = []

    for unit in units:
        breadcrumb = unit.breadcrumb()
        situating_context = situate_unit(llm, unit)

        for piece in split_body(unit.body()):
            header = f"[{unit.source}] {breadcrumb}\nContext: {situating_context}"
            text_for_index = f"{header}\n\n{piece}"
            chunks.append(
                ContextualChunk(
                    text_for_index=text_for_index,
                    raw_text=piece,
                    metadata={
                        "source": unit.source,
                        "clause_number": unit.clause_number,
                        "breadcrumb": breadcrumb,
                        "situating_context": situating_context,
                        "page": unit.page,
                    },
                )
            )

    return chunks


if __name__ == "__main__":
    from pathlib import Path

    from app.kb.parse import parse_document

    units = parse_document(Path("documents/Wimmera CMA Enterprise Agreement 2024-2028.pdf"))
    sample = [unit for unit in units if unit.clause_number in ("23.3",) or "Appendix C" in unit.breadcrumb()][:2]
    for chunk in build_contextual_chunks(sample):
        print("----")
        print(chunk.text_for_index[:500])
