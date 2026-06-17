import asyncio
import json

from sqlalchemy import delete

from app.db import async_session_maker, create_db_and_tables
from app.kb.bm25_index import BM25_CORPUS_PATH
from app.kb.clause_model import extract_cross_refs
from app.models import Clause


def title_from_breadcrumb(breadcrumb: str, clause_number: str) -> str:
    last_segment = breadcrumb.split(" > ")[-1].strip()
    if clause_number and last_segment.startswith(clause_number):
        return last_segment[len(clause_number):].strip()
    return last_segment


def rebuild_clause_records() -> list[dict]:
    records = json.loads(BM25_CORPUS_PATH.read_text(encoding="utf-8"))

    grouped: dict[tuple, dict] = {}
    for record in records:
        meta = record["metadata"]
        key = (meta["source"], meta["clause_number"], meta["breadcrumb"])
        if key not in grouped:
            grouped[key] = {
                "source": meta["source"],
                "clause_number": meta["clause_number"],
                "title": title_from_breadcrumb(meta["breadcrumb"], meta["clause_number"]),
                "breadcrumb": meta["breadcrumb"],
                "scope": meta.get("scope", "general"),
                "condition": meta.get("condition", ""),
                "page": meta.get("page", 0),
                "text_pieces": [],
            }
        grouped[key]["text_pieces"].append(record["raw_text"])

    clause_records = []
    for group in grouped.values():
        full_text = "\n".join(group.pop("text_pieces"))
        group["full_text"] = full_text
        group["cross_refs"] = ",".join(extract_cross_refs(full_text, group["clause_number"]))
        clause_records.append(group)
    return clause_records


async def store(clause_records: list[dict]):
    await create_db_and_tables()
    async with async_session_maker() as db:
        await db.execute(delete(Clause))
        for record in clause_records:
            db.add(Clause(**record))
        await db.commit()


if __name__ == "__main__":
    clause_records = rebuild_clause_records()
    asyncio.run(store(clause_records))
    print(f"Stored {len(clause_records)} clause records from the BM25 corpus.")
