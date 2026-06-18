import asyncio

from llama_index.core.llms import ChatMessage, MessageRole

from app.db import async_session_maker
from app.rag.chat import DEFAULT_SYSTEM_PROMPT, UNSURE_RESPONSE
from app.rag.pipeline import produce_grounded_answer


CASES = [
    {
        "name": "Bug1: lunch break governed by clause 23, not emergency Appendix C (Arif's verbatim wording)",
        "category": "scope",
        "question": (
            "say i worked between 8 AM - 4 PM, with lunch between 12-12:30 pm. "
            "will the lunch counted as worked hours or non worked hours?"
        ),
        "expect_contains_any": ["unpaid", "does not count", "not count", "non-worked", "non worked", "23.2"],
        "expect_absent_all": ["AIIMS", "Appendix C", "counted as time worked"],
        "expect_abstain": False,
    },
    {
        "name": "Issue#1: emergency-work meal break counts as worked time (clause 1.5), opposite of the normal day",
        "category": "scope",
        "history": [
            (
                "user",
                "say i worked between 8 AM - 4 PM, with lunch between 12-12:30 pm. "
                "will the lunch counted as worked hours or non worked hours?",
            ),
            ("assistant", "Your lunch break would be counted as non-worked hours (clause 23.2)."),
        ],
        "question": "what would be the case during emergency work",
        "expect_contains_any": ["counted as time worked", "1.5", "part of your working", "time worked"],
        "expect_absent_all": ["could not find"],
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
        "expect_absent_all": ["password is "],
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
        "name": "broad topic gets a real overview, not a dead-end",
        "category": "overview",
        "question": "Tell me about leaves and breaks.",
        "expect_contains_any": ["leave", "break"],
        "expect_absent_all": ["could not find"],
        "expect_abstain": False,
    },
    {
        "name": "Bug2: coverage/count answered from the KB map, not abstained (Arif's verbatim follow-up)",
        "category": "coverage",
        "history": [
            ("user", "tell me about leaves and breaks"),
            (
                "assistant",
                "Wimmera CMA covers several types of leave (annual, personal/carer's, parental, "
                "compassionate, long service, and more) and rest/meal breaks under the enterprise agreement.",
            ),
        ],
        "question": "how many of them we got",
        "expect_contains_any": ["leave", "type", "annual", "personal"],
        "expect_absent_all": ["could not find"],
        "expect_abstain": False,
    },
    {
        "name": "guided tour offer is honoured with a walkthrough",
        "category": "tour",
        "question": "Give me a short guided tour of what's covered.",
        "expect_contains_any": ["leave", "hours", "pay", "polic", "enterprise"],
        "expect_absent_all": ["could not find", "don't cover", "do not cover tours"],
        "expect_abstain": False,
    },
    {
        "name": "annual leave is covered and answered",
        "category": "coverage",
        "question": "How is annual leave accrued under the enterprise agreement?",
        "expect_contains_any": ["annual leave", "accru", "36"],
        "expect_abstain": False,
    },
    {
        "name": "compound question: ordinary-day AND emergency meal break in one turn (both answered)",
        "category": "scope",
        "question": (
            "say i worked between 8 AM - 4 PM, with lunch between 12-12:30 pm. "
            "will the lunch counted as worked hours or non worked hours? "
            "also what would be the case during emergency work."
        ),
        "expect_contains_all_groups": [
            ["non-worked", "non worked", "unpaid", "not count", "23.2"],
            ["counted as time worked", "time worked", "1.5", "paid"],
        ],
        "expect_absent_all": ["could not find"],
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

    for group in case.get("expect_contains_all_groups", []):
        if not any(term.lower() in lowered for term in group):
            return False, f"missing all of {group}"

    return True, "ok"


def build_history(case: dict) -> list[ChatMessage]:
    history = []
    for role, content in case.get("history", []):
        message_role = MessageRole.USER if role == "user" else MessageRole.ASSISTANT
        history.append(ChatMessage(role=message_role, content=content))
    return history


async def run_eval():
    results_by_category: dict[str, list[bool]] = {}

    async with async_session_maker() as db:
        for case in CASES:
            history = build_history(case)
            answer = await produce_grounded_answer(
                db, history, "", DEFAULT_SYSTEM_PROMPT, case["question"]
            )
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
