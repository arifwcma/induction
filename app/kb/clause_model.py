import re

from app.kb.contextual import SituatingResult
from app.kb.parse import ClauseUnit


CROSS_REF = re.compile(r"clause\s+(\d{1,2}(?:\.\d{1,2}){0,3})", re.IGNORECASE)


def extract_cross_refs(text: str, own_number: str) -> list[str]:
    found = []
    for match in CROSS_REF.finditer(text):
        number = match.group(1)
        if number != own_number and number not in found:
            found.append(number)
    return found


def build_clause_record(unit: ClauseUnit, situating: SituatingResult) -> dict:
    body = unit.body()
    return {
        "source": unit.source,
        "clause_number": unit.clause_number,
        "title": unit.title,
        "breadcrumb": unit.breadcrumb(),
        "scope": situating.scope,
        "condition": situating.condition,
        "page": unit.page,
        "full_text": body,
        "cross_refs": ",".join(extract_cross_refs(body, unit.clause_number)),
    }
