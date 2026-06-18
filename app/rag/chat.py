from dataclasses import dataclass

from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.llms.openai import OpenAI

from app.config import get_settings
from app.models import Clause
from app.rag.retrieval import Passage


DEFAULT_SYSTEM_PROMPT = (
    "You are the induction assistant for new employees at the Wimmera Catchment Management "
    "Authority (Wimmera CMA). You help people understand organisational policies, procedures, and "
    "the enterprise agreement.\n\n"
    "With each question you are given two things: (1) a knowledge base MAP listing the documents and "
    "the topics/sections each one covers, and (2) SOURCE MATERIAL - specific passages retrieved for "
    "this question.\n"
    "- The MAP is the authoritative, complete list of what exists. Use it to say what is covered, to "
    "give overviews, to LIST and COUNT topics or section types (e.g. how many kinds of leave exist), "
    "and to walk someone through topics. You may confidently enumerate and count items that appear in "
    "the map. The map is structure, not rule detail - never quote specific rules, numbers, durations, "
    "or entitlements from it.\n"
    "- Use the SOURCE MATERIAL for every SUBSTANTIVE fact (a rule, amount, duration, eligibility, "
    "condition, or entitlement), and cite it.\n"
    "- Never invent facts.\n\n"
    "How to respond (use judgement, be genuinely helpful):\n"
    "- Greetings or 'what can you help with': briefly say what you cover (draw on the map) and invite "
    "a question. You CAN offer and give a short guided walkthrough of the main topics when asked - "
    "summarise the areas from the map and let the person pick where to go deeper. Honour anything an "
    "earlier greeting offered (such as a short guided tour).\n"
    "- Broad or open questions ('tell me about leave and breaks', 'give me an overall idea', 'how "
    "many types of leave are there'): give a real, useful overview. Summarise the relevant topics "
    "from the map together with whatever substance is in the source material, then offer to go "
    "deeper. Do NOT refuse a broad question or bounce it back with only a clarifying question - "
    "answer first, then optionally ask what they want next.\n"
    "- Specific questions: answer directly and concisely from the source material, with citations.\n"
    "- Ask a clarifying question only when the request is genuinely ambiguous AND you cannot give a "
    "useful partial answer. Prefer answering first, then narrowing.\n"
    "- Out of scope (e.g. IT passwords, building keys, personal HR cases): say plainly it is not "
    "covered by the induction materials and point them to their manager or People & Culture.\n\n"
    "Be concise and plain. Use the conversation so far; do not re-ask what the person already told you.\n\n"
    "Choosing the governing rule (critical for correctness):\n"
    "- Each source passage states its SCOPE. A passage marked 'general' applies to ordinary "
    "situations. A passage marked 'conditional' applies ONLY when its stated condition is actually "
    "true for the asked situation.\n"
    "- Never apply a conditional passage to a situation where its condition does not hold. If the "
    "question describes an ordinary situation, use the general provision even if a conditional "
    "passage looks textually similar.\n"
    "- Provisions about emergency work, incident response, or AIIMS activation (including any "
    "appendix marked conditional) apply ONLY when the employee's own situation is an actual "
    "emergency activation. For ordinary day-to-day questions you MUST ignore those provisions "
    "entirely and answer only from the general provisions, even if the emergency text matches the "
    "wording more closely. Do not cite numbering that appears inside such an appendix.\n"
    "- When provisions interact, the more specific governing provision wins; and where the National "
    "Employment Standards (NES) give a greater benefit, the NES prevails (see clause 4.3).\n"
    "- If you rely on a conditional provision, state the condition explicitly.\n\n"
    "Citing sources:\n"
    "- For every substantive factual claim, cite the clause number or section and the document it "
    "came from. If information came from trainer-added knowledge, say so.\n"
    "- For overviews or navigation drawn from the map, you do not need clause citations - just name "
    "the topics or sections.\n\n"
    "If the source material does not contain a specific answer the person needs, say so plainly and "
    "point them to their manager or People & Culture rather than guessing."
)

CONDENSE_INSTRUCTION = (
    "Given the conversation so far and a follow-up message, rewrite the follow-up as a single "
    "standalone question understandable without the conversation. Keep the original wording where "
    "possible. Return only the rewritten question.\n\n"
    "Conversation so far:\n{transcript}\n\nFollow-up message: {message}\n\nStandalone question:"
)

SEARCH_QUERY_INSTRUCTION = (
    "Turn the employee's question into a concise search query for a policy/HR knowledge base. "
    "Keep the policy TOPIC and key terms (for example: meal break, lunch, ordinary hours, time "
    "worked, annual leave, allowance). Drop narrative scenario details such as specific times, "
    "dates, and phrasing like 'say I worked'. Expand obvious everyday synonyms to the likely policy "
    "wording (for example 'lunch' -> 'meal break'). Return only the query, a few keywords or a short "
    "phrase, with no preamble.\n\n"
    "Employee question: {question}\n\nSearch query:"
)

UNSURE_RESPONSE = (
    "I could not find this clearly in the induction material, so I do not want to guess. Could you "
    "rephrase, or tell me which policy or situation you mean? For anything personal or not covered "
    "by the documents, your manager or People & Culture is the right place to ask."
)

VERIFIER_INSTRUCTION = (
    "You are a reviewer checking an answer for an HR induction assistant. Decide whether the answer "
    "is safe to send.\n\n"
    "You are given a KNOWLEDGE BASE MAP and SOURCE MATERIAL. They have different authority:\n"
    "- The MAP is the authoritative, complete list of the documents that exist and the topics / "
    "sections each one covers. It is trustworthy for WHAT EXISTS and HOW MANY: which topics are "
    "covered, listing them, and counting them. The map lists every section, so a count or list drawn "
    "from it is correct even though no policy passage was retrieved for each item.\n"
    "- The SOURCE MATERIAL is the retrieved passages and is authoritative for SUBSTANTIVE POLICY "
    "FACTS: specific rules, numbers, durations, rates, eligibility, conditions, entitlements, and "
    "procedures.\n\n"
    "Classify each claim in the answer and judge it against the right authority:\n"
    "1. EXISTENCE / COVERAGE / ENUMERATION claims - that a topic, section, or leave type is covered; "
    "a LIST of such topics or leave-type NAMES; or a COUNT like 'there are 14 types of leave'. The "
    "NAME and EXISTENCE of a leave type, section, or topic is a coverage claim, NOT a policy fact. "
    "Grade these ONLY against the MAP: if the named items appear as sections/topics in the map, the "
    "list and its count are CORRECT - PASS them. The map is complete and authoritative, so do NOT "
    "require a source passage for each listed item and do NOT call a list of leave-type names a "
    "'substantive policy fact'. When a coverage/list/count answer's items are all in the map, you "
    "MUST pass it.\n"
    "2. SUBSTANTIVE POLICY claims - what a rule actually SAYS about a topic: amounts, durations, "
    "rates, eligibility, conditions, entitlements, procedures (e.g. 'meal breaks are unpaid', "
    "'20-minute paid rest break', 'annual leave accrues at X'). These MUST be supported by the SOURCE "
    "MATERIAL. Fail any substantive fact the source material does not support.\n\n"
    "FAIL the answer only if:\n"
    "- A SUBSTANTIVE policy fact (a rule's content, not the mere existence/name of a topic) is not "
    "supported by the SOURCE MATERIAL, OR\n"
    "- SCOPE VIOLATION (most important): the answer's substance is drawn from a passage marked "
    "'conditional' (for example an emergency / AIIMS / incident-response appendix) while the question "
    "describes an ordinary, non-emergency situation. If the question is about a normal working day and "
    "the answer relies on emergency or appendix content, you MUST fail it - even if the wording matches, OR\n"
    "- It names a topic, section, clause, or document that appears in NEITHER the map NOR the source "
    "material (a genuine fabrication).\n\n"
    "Be lenient on minor citation imprecision, on high-level overviews, and on lists/counts of topics "
    "that come from the map. Never be lenient about scope violations or about invented substantive facts.\n\n"
    "Reply with exactly one line: 'VERDICT: pass' or 'VERDICT: fail - <short reason>'.\n\n"
    "Knowledge base map:\n{kb_map}\n\nSource material:\n{context}\n\nQuestion:\n{question}\n\n"
    "Answer under review:\n{answer}\n\nVerdict:"
)


@dataclass
class VerifierVerdict:
    passed: bool
    reason: str


FIXED_SEED = 7


def build_llm() -> OpenAI:
    settings = get_settings()
    return OpenAI(
        model=settings.openai_chat_model,
        api_key=settings.openai_api_key,
        temperature=0,
        additional_kwargs={"seed": FIXED_SEED},
    )


def format_transcript(history: list[ChatMessage]) -> str:
    lines = []
    for message in history:
        speaker = "Employee" if message.role == MessageRole.USER else "Assistant"
        lines.append(f"{speaker}: {message.content}")
    return "\n".join(lines)


def condense_to_standalone_question(llm: OpenAI, history: list[ChatMessage], message: str) -> str:
    if not history:
        return message
    prompt = CONDENSE_INSTRUCTION.format(transcript=format_transcript(history), message=message)
    return llm.complete(prompt).text.strip()


def build_search_query(llm: OpenAI, question: str) -> str:
    prompt = SEARCH_QUERY_INSTRUCTION.format(question=question)
    return llm.complete(prompt).text.strip()


def passage_scope_line(metadata: dict) -> str:
    if metadata.get("scope") == "conditional":
        condition = metadata.get("condition") or "a specific condition"
        return f"SCOPE: conditional - applies only when {condition}"
    return "SCOPE: general"


def passage_label(metadata: dict) -> str:
    if metadata.get("origin") == "trainer":
        return f"{metadata.get('source', 'trainer note')} (trainer-provided)"
    source = metadata.get("source", "document")
    clause_number = metadata.get("clause_number")
    if clause_number:
        return f"{source}, clause {clause_number}"
    if metadata.get("page"):
        return f"{source}, p.{metadata['page']}"
    return source


def format_context(passages: list[Passage], clauses: list[Clause]) -> str:
    blocks = []
    for passage in passages:
        label = passage_label(passage.metadata)
        scope_line = passage_scope_line(passage.metadata)
        blocks.append(f"[{label}]\n{scope_line}\n{passage.raw_text}")

    for clause in clauses:
        scope_line = (
            f"SCOPE: conditional - applies only when {clause.condition}"
            if clause.scope == "conditional"
            else "SCOPE: general"
        )
        label = f"{clause.source}, clause {clause.clause_number}" if clause.clause_number else clause.source
        blocks.append(f"[{label} (full clause)]\n{scope_line}\n{clause.full_text}")

    return "\n\n".join(blocks)


def generate_answer(
    system_prompt: str,
    history: list[ChatMessage],
    context_block: str,
    message: str,
    kb_map: str = "",
) -> str:
    llm = build_llm()
    messages = [ChatMessage(role=MessageRole.SYSTEM, content=system_prompt)]
    if kb_map:
        messages.append(
            ChatMessage(
                role=MessageRole.SYSTEM,
                content=(
                    "Knowledge base map (topics available; for overviews and navigation only, "
                    f"NOT a source of facts):\n\n{kb_map}"
                ),
            )
        )
    messages.extend(
        [
            ChatMessage(role=MessageRole.SYSTEM, content=f"Source material:\n\n{context_block}"),
            *history,
            ChatMessage(role=MessageRole.USER, content=message),
        ]
    )
    return llm.chat(messages).message.content.strip()


def verify_answer(context_block: str, question: str, answer: str, kb_map: str = "") -> VerifierVerdict:
    llm = build_llm()
    prompt = VERIFIER_INSTRUCTION.format(
        kb_map=kb_map or "(none)", context=context_block, question=question, answer=answer
    )
    verdict_text = llm.complete(prompt).text.strip()
    passed = "verdict: pass" in verdict_text.lower()
    reason = verdict_text.split("-", 1)[1].strip() if "-" in verdict_text else ""
    return VerifierVerdict(passed=passed, reason=reason)


def stream_in_pieces(text: str):
    for word in text.split(" "):
        yield word + " "


def summarise_conversation(history: list[ChatMessage]) -> str:
    if not history:
        return ""
    llm = build_llm()
    prompt = (
        "Summarise the following conversation in two or three sentences, capturing what the employee "
        "asked about and any personal context they shared. Do not add anything not said.\n\n"
        f"Conversation:\n{format_transcript(history)}\n\nSummary:"
    )
    return llm.complete(prompt).text.strip()
