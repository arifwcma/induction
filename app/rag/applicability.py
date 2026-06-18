from app.models import Clause
from app.rag.chat import build_fast_llm
from app.rag.retrieval import Passage


APPLICABILITY_PROMPT = (
    "You are filtering policy provisions before they are used to answer an employee's question. "
    "A provision has been tagged as applying in a particular situation, and you must decide whether "
    "including it could MISLEAD the employee.\n\n"
    "Employee's question:\n{question}\n\n"
    "Provision location (the document section this provision sits under):\n{breadcrumb}\n\n"
    "This provision is tagged as applying when: {condition}\n\n"
    "Use the provision location to understand what the tag really means. A tag can be terse or cryptic "
    "(an acronym, a system name, a code) - the section heading usually makes its meaning plain (e.g. a "
    "tag like 'AIMS control system' under a section titled 'Emergency Work' simply means emergency work).\n\n"
    "DEFAULT TO KEEPING the provision. Answer 'no' (exclude) ONLY when the provision clearly belongs to "
    "a SPECIAL or DIFFERENT scenario than the question is about, so that applying it would give a wrong "
    "answer - for example, emergency-only provisions when the question is about an ordinary working day, "
    "or a different leave type than the one being asked about.\n"
    "Answer 'yes' (keep) in all other cases. In particular keep it when:\n"
    "- the provision merely notes which employees or timeframe it normally applies to (e.g. 'non-casual "
    "employees', 'ongoing staff', 'after probation') but is otherwise the relevant provision; or\n"
    "- the question is explicitly about the tagged scenario (e.g. asking what happens during emergency work).\n"
    "Reply with one word: 'yes' or 'no'."
)


def condition_applies(
    llm, question: str, condition: str, breadcrumb: str, cache: dict[str, bool]
) -> bool:
    key = f"{breadcrumb.strip().lower()}||{condition.strip().lower()}"
    if not condition.strip():
        return True
    if key in cache:
        return cache[key]
    prompt = APPLICABILITY_PROMPT.format(
        question=question, breadcrumb=breadcrumb or "(unspecified)", condition=condition
    )
    verdict = llm.complete(prompt).text.strip().lower()
    applies = verdict.startswith("yes")
    cache[key] = applies
    return applies


def keep_applicable(question: str, passages: list[Passage], clauses: list[Clause]):
    llm = build_fast_llm()
    cache: dict[str, bool] = {}

    kept_passages = []
    for passage in passages:
        if passage.metadata.get("scope") != "conditional":
            kept_passages.append(passage)
            continue
        if condition_applies(
            llm,
            question,
            passage.metadata.get("condition", ""),
            passage.metadata.get("breadcrumb", ""),
            cache,
        ):
            kept_passages.append(passage)

    kept_clauses = []
    for clause in clauses:
        if clause.scope != "conditional":
            kept_clauses.append(clause)
            continue
        if condition_applies(llm, question, clause.condition, clause.breadcrumb, cache):
            kept_clauses.append(clause)

    return kept_passages, kept_clauses
