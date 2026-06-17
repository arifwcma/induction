from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Clause
from app.rag.retrieval import Passage


MAX_EXPANDED_CLAUSES = 12


def parent_prefix(clause_number: str) -> str:
    if "." in clause_number:
        return clause_number.rsplit(".", 1)[0]
    return clause_number


async def fetch_clause(db: AsyncSession, source: str, clause_number: str) -> Clause | None:
    if not clause_number:
        return None
    query = select(Clause).where(Clause.source == source, Clause.clause_number == clause_number)
    return (await db.execute(query)).scalars().first()


async def fetch_sibling_clauses(db: AsyncSession, source: str, clause_number: str) -> list[Clause]:
    prefix = parent_prefix(clause_number)
    if not prefix:
        return []
    query = select(Clause).where(
        Clause.source == source,
        (Clause.clause_number == prefix) | (Clause.clause_number.like(f"{prefix}.%")),
    )
    return list((await db.execute(query)).scalars().all())


def collect_clause_numbers(passages: list[Passage]) -> list[tuple[str, str]]:
    ordered = []
    for passage in passages:
        source = passage.metadata.get("source", "")
        number = passage.metadata.get("clause_number", "")
        if number and (source, number) not in ordered:
            ordered.append((source, number))
    return ordered


async def expand_clauses(db: AsyncSession, passages: list[Passage]) -> list[Clause]:
    expanded: dict[tuple[str, str], Clause] = {}

    for source, number in collect_clause_numbers(passages):
        for sibling in await fetch_sibling_clauses(db, source, number):
            expanded[(sibling.source, sibling.clause_number)] = sibling

        clause = await fetch_clause(db, source, number)
        if clause is not None:
            for cross_ref in clause.cross_refs.split(","):
                cross_ref = cross_ref.strip()
                if not cross_ref or (source, cross_ref) in expanded:
                    continue
                referenced = await fetch_clause(db, source, cross_ref)
                if referenced is not None:
                    expanded[(source, cross_ref)] = referenced

        if len(expanded) >= MAX_EXPANDED_CLAUSES:
            break

    return list(expanded.values())
