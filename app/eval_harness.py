import asyncio

from app.db import async_session_maker
from app.rag.chat import DEFAULT_SYSTEM_PROMPT, UNSURE_RESPONSE
from app.rag.pipeline import produce_grounded_answer


CASES = [
    {
        "name": "meal break governed by clause 23, not emergency Appendix C",
        "category": "scope",
        "question": (
            "I attended the office at 8 AM and left at 4 PM, with lunch from 12:00 to 12:30. "
            "On a normal day, does my lunch break count as time worked?"
        ),
        "expect_contains_any": ["unpaid", "does not count", "not count", "23.2"],
        "expect_absent_all": ["AIIMS", "Appendix C", "counted as time worked"],
        "expect_abstain": False,
    },
    {
        "name": "ordinary hours question not answered from emergency provisions",
        "category": "scope",
        "question": "On a normal working day, what are my standard hours of work?",
        "expect_contains_any": ["hours", "21"],
        "expect_absent_all": ["AIIMS", "emergency response"],
        "expect_abstain": False,
    },
    {
        "name": "out of scope question is declined and redirected",
        "category": "out-of-scope",
        "question": "What is the wifi password for the Melbourne office?",
        "expect_contains_any": ["not", "IT", "manager", "People", "cover"],
        "expect_absent_all": ["password is"],
        "expect_abstain": False,
    },
    {
        "name": "capability question gets a helpful overview, not a dead-end",
        "category": "meta",
        "question": "What can you help me with?",
        "expect_contains_any": ["help", "leave", "polic", "enterprise", "hours"],
        "expect_absent_all": ["could not find"],
        "expect_abstain": False,
    },
    {
        "name": "broad topic prompts a focused clarification, not a dead-end",
        "category": "clarify",
        "question": "Tell me about leaves and breaks.",
        "expect_absent_all": ["could not find"],
        "expect_abstain": False,
    },
    {
        "name": "annual leave is covered and answered",
        "category": "coverage",
        "question": "How is annual leave accrued under the enterprise agreement?",
        "expect_contains_any": ["annual leave", "accru", "36"],
        "expect_abstain": False,
    },
]


def evaluate(case: dict, answer: str) -> tuple[bool, str]:
    lowered = answer.lower()
    abstained = answer.strip() == UNSURE_RESPONSE.strip()

    if case.get("expect_abstain"):
        if abstained:
            return True, "abstained as expected"
        return False, "expected abstention but answered"

    if abstained:
        return False, "abstained but an answer was expected"

    for forbidden in case.get("expect_absent_all", []):
        if forbidden.lower() in lowered:
            return False, f"contained forbidden term '{forbidden}'"

    contains_any = case.get("expect_contains_any", [])
    if contains_any and not any(term.lower() in lowered for term in contains_any):
        return False, f"missing any of {contains_any}"

    return True, "ok"


async def run_eval():
    results_by_category: dict[str, list[bool]] = {}

    async with async_session_maker() as db:
        for case in CASES:
            answer = await produce_grounded_answer(db, [], "", DEFAULT_SYSTEM_PROMPT, case["question"])
            passed, detail = evaluate(case, answer)
            results_by_category.setdefault(case["category"], []).append(passed)

            print(f"\n=== [{case['category']}] {case['name']} ===")
            print(f"Q: {case['question']}")
            print(f"A: {answer[:300]}")
            print(f"{'PASS' if passed else 'FAIL'} - {detail}")

    print("\n--- per-category pass rates ---")
    total_passed = 0
    total = 0
    for category, results in results_by_category.items():
        passed = sum(1 for r in results if r)
        total_passed += passed
        total += len(results)
        print(f"{category}: {passed}/{len(results)}")
    print(f"OVERALL: {total_passed}/{total}")


if __name__ == "__main__":
    asyncio.run(run_eval())
