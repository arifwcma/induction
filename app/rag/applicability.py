from app.models import Clause
from app.rag.chat import build_llm
from app.rag.retrieval import Passage


APPLICABILITY_PROMPT = (
    "An organisational policy provision applies ONLY under a specific condition. Decide whether this "
    "provision should be used to answer the employee's question.\n\n"
    "Employee's question:\n{question}\n\n"
    "The provision applies only when: {condition}\n\n"
    "Answer 'yes' if EITHER the employee's situation clearly meets that condition OR the question is "
    "explicitly asking about that conditional scenario/topic (for example, asking what happens during "
    "emergency work when the condition is about emergencies). Answer 'no' only if the question is "
    "about an ordinary situation that does not involve this condition. Reply with one word: 'yes' or 'no'."
)


def condition_applies(llm, question: str, condition: str, cache: dict[str, bool]) -> bool:
    key = condition.strip().lower()
    if not key:
        return True
    if key in cache:
        return cache[key]
    prompt = APPLICABILITY_PROMPT.format(question=question, condition=condition)
    verdict = llm.complete(prompt).text.strip().lower()
    applies = verdict.startswith("yes")
    cache[key] = applies
    return applies


def keep_applicable(question: str, passages: list[Passage], clauses: list[Clause]):
    llm = build_llm()
    cache: dict[str, bool] = {}

    kept_passages = []
    for passage in passages:
        if passage.metadata.get("scope") != "conditional":
            kept_passages.append(passage)
            continue
        if condition_applies(llm, question, passage.metadata.get("condition", ""), cache):
            kept_passages.append(passage)

    kept_clauses = []
    for clause in clauses:
        if clause.scope != "conditional":
            kept_clauses.append(clause)
            continue
        if condition_applies(llm, question, clause.condition, cache):
            kept_clauses.append(clause)

    return kept_passages, kept_clauses
