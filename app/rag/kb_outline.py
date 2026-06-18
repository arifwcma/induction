"""Builds a compact structural map of the knowledge base.

The outline lists the documents and the topics/sections each one covers so the
model can reason about coverage, give overviews, and walk a user through topics.
It is derived from the stored clause table (which already carries LLM-generated
titles for any unit that lacked a heading), so it works even for poorly
structured documents. It is a MAP only -- never a source of factual content.
"""

from sqlalchemy import select

from app.models import Clause


_cached_outline: str | None = None


def section_label(clause: Clause) -> str:
    root = clause.breadcrumb.split(" > ")[0].strip() if clause.breadcrumb else ""
    if root:
        return root
    if clause.title.strip():
        return clause.title.strip()
    return ""


def document_section_labels(clauses: list[Clause], source: str) -> list[str]:
    ordered_labels = []
    source_clauses = [clause for clause in clauses if clause.source == source]
    source_clauses.sort(key=lambda clause: (clause.page, clause.clause_number))
    for clause in source_clauses:
        label = section_label(clause)
        if label and label not in ordered_labels:
            ordered_labels.append(label)
    return ordered_labels


def render_outline(clauses: list[Clause]) -> str:
    sources = []
    for clause in clauses:
        if clause.source not in sources:
            sources.append(clause.source)
    sources.sort()

    blocks = []
    for source in sources:
        labels = document_section_labels(clauses, source)
        if not labels:
            continue
        document_name = source.rsplit(".", 1)[0]
        listed = "\n".join(f"  - {label}" for label in labels)
        blocks.append(f"{document_name}:\n{listed}")

    if not blocks:
        return ""

    return (
        "Knowledge base map (the documents available and the topics each covers). "
        "Use this only to understand what exists and to guide overviews or a walkthrough; "
        "it is NOT a source of factual answers -- never quote rules from it.\n\n"
        + "\n\n".join(blocks)
    )


async def get_kb_outline(db) -> str:
    global _cached_outline
    if _cached_outline is not None:
        return _cached_outline
    clauses = list((await db.execute(select(Clause))).scalars().all())
    _cached_outline = render_outline(clauses)
    return _cached_outline


def reset_outline_cache():
    global _cached_outline
    _cached_outline = None
