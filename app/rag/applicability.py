import asyncio

from starlette.concurrency import run_in_threadpool

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


def _cache_key(condition: str, breadcrumb: str) -> str:
    return f"{breadcrumb.strip().lower()}||{condition.strip().lower()}"


def _judge_condition(llm, question: str, condition: str, breadcrumb: str) -> bool:
    prompt = APPLICABILITY_PROMPT.format(
        question=question, breadcrumb=breadcrumb or "(unspecified)", condition=condition
    )
    verdict = llm.complete(prompt).text.strip().lower()
    return verdict.startswith("yes")


def _conditional_items(passages: list[Passage], clauses: list[Clause]):
    """Yield (condition, breadcrumb) for every conditional passage/clause."""
    for passage in passages:
        if passage.metadata.get("scope") == "conditional":
            yield passage.metadata.get("condition", ""), passage.metadata.get("breadcrumb", "")
    for clause in clauses:
        if clause.scope == "conditional":
            yield clause.condition, clause.breadcrumb


async def keep_applicable(question: str, passages: list[Passage], clauses: list[Clause]):
    """Drop conditional provisions that belong to a different scenario than the
    question. The per-condition judgments are independent, so they run
    concurrently (one fast-lane call per *unique* condition) instead of in series."""
    llm = build_fast_llm()

    # Collect the unique conditions that need a judgment.
    unique: dict[str, tuple[str, str]] = {}
    for condition, breadcrumb in _conditional_items(passages, clauses):
        if condition.strip():
            unique.setdefault(_cache_key(condition, breadcrumb), (condition, breadcrumb))

    async def judge(key: str, condition: str, breadcrumb: str) -> tuple[str, bool]:
        applies = await run_in_threadpool(_judge_condition, llm, question, condition, breadcrumb)
        return key, applies

    results = await asyncio.gather(
        *(judge(key, condition, breadcrumb) for key, (condition, breadcrumb) in unique.items())
    )
    cache: dict[str, bool] = dict(results)

    def applies(condition: str, breadcrumb: str) -> bool:
        if not condition.strip():
            return True
        return cache.get(_cache_key(condition, breadcrumb), True)

    kept_passages = [
        passage
        for passage in passages
        if passage.metadata.get("scope") != "conditional"
        or applies(passage.metadata.get("condition", ""), passage.metadata.get("breadcrumb", ""))
    ]
    kept_clauses = [
        clause
        for clause in clauses
        if clause.scope != "conditional" or applies(clause.condition, clause.breadcrumb)
    ]
    return kept_passages, kept_clauses
