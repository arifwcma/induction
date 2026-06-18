import asyncio

from llama_index.core.llms import ChatMessage, MessageRole

from app.db import async_session_maker
from app.rag.chat import DEFAULT_SYSTEM_PROMPT, UNSURE_RESPONSE
from app.rag.pipeline import produce_grounded_answer


GREETING = (
    "Hi there, and welcome to Wimmera CMA! I'm your induction assistant. Ask me anything about our "
    "organisational policies and procedures - or, if you'd prefer, I can walk you through them with "
    "a short guided tour. Where would you like to start?"
)

CASE_1 = [
    "tell me about leaves and breaks",
    "how many of them we got",
    "give me an overall idea on leaves and breaks",
]

CASE_2_OPENING = GREETING
CASE_2 = ["give me the tour you offerred"]

CASE_3 = [
    "say i worked between 8 AM - 4 PM, with lunch between 12-12:30 pm. "
    "will the lunch counted as worked hours or non worked hours?"
]

# Issue#1: emergency-work follow-up to the lunch question.
CASE_4 = [
    "say i worked between 8 AM - 4 PM, with lunch between 12-12:30 pm. "
    "will the lunch counted as worked hours or non worked hours?",
    "what would be the case during emergency work",
]

# Issue#2 + #2.2: emergency-work overview, then a tour request with NO greeting in
# history (matches the real app, where the greeting is frontend-only).
CASE_5 = [
    "tell me about emergency work",
    "okay lets talk about the short tours",
]

# Issue#3: broad open topic should get a short overview first, not only a clarifier.
CASE_6 = ["lets talk about leaves"]

# Compound single-turn: ordinary-day meal break AND emergency work in one message.
# Both parts must be answered (emergency meal = counted as time worked, clause 1.5).
CASE_7 = [
    "say i worked between 8 AM - 4 PM, with lunch between 12-12:30 pm. "
    "will the lunch counted as worked hours or non worked hours? "
    "also what would be the case during emergency work."
]

# Case#8: single-intent EMERGENCY scenario (the inverse framing of Case#3). The
# answer must be that the meal break IS counted as worked time (clause 1.5), NOT
# the ordinary-day "unpaid/non-worked" rule.
CASE_8 = [
    "say during an emergency work, i worked between 8 AM - 4 PM, with lunch "
    "between 12-12:30 pm. will the lunch counted as worked hours or non worked hours?"
]

# Cases 9-11: tour requests phrased various ways (should honour the guided tour).
CASE_9 = ["i want short guided tour"]
CASE_10 = ["lets talk about leaves", "give an overview", "lets gor for the short tour you talked about"]
CASE_11 = ["short tour"]

# Case#12: conversational recap. After a real Q&A, "what were we talking about?"
# must be answered from the conversation (NOT abstained) - the history-aware
# verifier should accept a recap grounded in the prior turns.
CASE_12 = [
    "How is annual leave accrued under the enterprise agreement?",
    "what were we talking about?",
]


def looks_like_abstention(answer: str) -> bool:
    return answer.strip() == UNSURE_RESPONSE.strip()


async def run_conversation(db, opening_assistant_message, user_messages):
    history = []
    if opening_assistant_message:
        history.append(ChatMessage(role=MessageRole.ASSISTANT, content=opening_assistant_message))
        print(f"ASSISTANT (greeting): {opening_assistant_message}\n")

    for user_message in user_messages:
        answer = await produce_grounded_answer(db, history, "", DEFAULT_SYSTEM_PROMPT, user_message)
        flag = "  <-- ABSTAINED" if looks_like_abstention(answer) else ""
        print(f"USER: {user_message}")
        print(f"ASSISTANT:{flag}\n{answer}\n")
        history.append(ChatMessage(role=MessageRole.USER, content=user_message))
        history.append(ChatMessage(role=MessageRole.ASSISTANT, content=answer))


async def run_smoke_cases():
    async with async_session_maker() as db:
        print("================ CASE 1 (overview / how many / overall idea) ================\n")
        await run_conversation(db, None, CASE_1)

        print("================ CASE 2 (guided tour) ================\n")
        await run_conversation(db, CASE_2_OPENING, CASE_2)

        print("================ CASE 3 (Bug1: lunch break) ================\n")
        await run_conversation(db, None, CASE_3)

        print("================ CASE 4 (Issue#1: emergency follow-up) ================\n")
        await run_conversation(db, None, CASE_4)

        print("================ CASE 5 (Issue#2 + #2.2: emergency overview, then tour) ================\n")
        await run_conversation(db, None, CASE_5)

        print("================ CASE 6 (Issue#3: broad topic overview first) ================\n")
        await run_conversation(db, None, CASE_6)

        print("================ CASE 7 (compound: ordinary + emergency in one turn) ================\n")
        await run_conversation(db, None, CASE_7)

        print("================ CASE 8 (single-intent emergency: meal = worked time) ================\n")
        await run_conversation(db, None, CASE_8)

        print("================ CASE 9 (tour request) ================\n")
        await run_conversation(db, None, CASE_9)

        print("================ CASE 10 (tour offer taken a few turns later) ================\n")
        await run_conversation(db, None, CASE_10)

        print("================ CASE 11 (short tour, lazy phrasing) ================\n")
        await run_conversation(db, None, CASE_11)

        print("================ CASE 12 (conversational recap from history) ================\n")
        await run_conversation(db, None, CASE_12)


if __name__ == "__main__":
    asyncio.run(run_smoke_cases())
