from app.rag.chat import DEFAULT_SYSTEM_PROMPT, answer_stream


CASES = [
    {
        "name": "meal-break governs over emergency appendix (Bug1)",
        "question": (
            "I work 8 hours and take a 30 minute lunch break from 12:00 to 12:30. "
            "Does that lunch count as time worked?"
        ),
        "expect_any_of": ["23.3", "consecutive", "break"],
        "must_not_anchor_on": ["AIIMS", "incident control", "emergency"],
    },
]


def collect_answer(question: str) -> str:
    return "".join(answer_stream(DEFAULT_SYSTEM_PROMPT, [], "", question))


def evaluate_case(case: dict) -> bool:
    answer = collect_answer(case["question"])
    lowered = answer.lower()

    mentions_governing_rule = any(token.lower() in lowered for token in case["expect_any_of"])
    anchored_on_emergency = any(token.lower() in lowered for token in case["must_not_anchor_on"])

    passed = mentions_governing_rule and not anchored_on_emergency

    print(f"\n=== {case['name']} ===")
    print(f"Q: {case['question']}")
    print(f"A: {answer}")
    print(f"PASS: {passed}")
    return passed


def run_regression():
    results = [evaluate_case(case) for case in CASES]
    passed_count = sum(1 for result in results if result)
    print(f"\n{passed_count}/{len(results)} cases passed.")


if __name__ == "__main__":
    run_regression()
