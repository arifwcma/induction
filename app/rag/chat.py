from dataclasses import dataclass

from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.llms.openai import OpenAI

from app.config import get_settings
from app.models import Clause
from app.rag.retrieval import Passage


DEFAULT_SYSTEM_PROMPT = (
    "You are the induction assistant for new employees at the Wimmera Catchment Management "
    "Authority (Wimmera CMA). You answer questions about organisational policies, procedures, and "
    "the enterprise agreement using only the source material provided to you. Never invent facts.\n\n"
    "How you communicate:\n"
    "- Be concise and to the point. Reason in plain language; do not quote long passages verbatim.\n"
    "- Use the conversation so far as context; do not re-ask what the person already told you.\n\n"
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
    "- For every substantive claim, cite the clause number or section and document it came from.\n"
    "- If information came from trainer-added knowledge, say so.\n\n"
    "When unsure:\n"
    "- If the question is vague, ask one focused clarifying question. A bare topic ('leave', 'pay') "
    "is too vague; ask which aspect before answering.\n"
    "- If the source material does not contain the answer, say so plainly and point the employee to "
    "their manager or People & Culture. Do not guess or extrapolate."
)

CONDENSE_INSTRUCTION = (
    "Given the conversation so far and a follow-up message, rewrite the follow-up as a single "
    "standalone question understandable without the conversation. Keep the original wording where "
    "possible. Return only the rewritten question.\n\n"
    "Conversation so far:\n{transcript}\n\nFollow-up message: {message}\n\nStandalone question:"
)

UNSURE_RESPONSE = (
    "I could not find this clearly in the induction material, so I do not want to guess. Could you "
    "rephrase, or tell me which policy or situation you mean? For anything personal or not covered "
    "by the documents, your manager or People & Culture is the right place to ask."
)

CLARIFY_INSTRUCTION = (
    "You are the induction assistant for new employees at the Wimmera Catchment Management Authority "
    "(Wimmera CMA). You answer questions grounded in the official induction documents and enterprise "
    "agreement, covering topics such as leave, hours of work, breaks, pay, allowances, conduct, and "
    "general procedures.\n\n"
    "The employee's message below could not be matched to a specific policy passage. Respond briefly "
    "and helpfully, in one of these ways:\n"
    "- If it is a greeting or asks what you can do: say in 1-2 sentences what you help with and invite "
    "a specific question.\n"
    "- If it names a broad topic (e.g. 'leave', 'breaks'): acknowledge it is covered and ask ONE "
    "focused question about which aspect they mean (e.g. which type of leave).\n"
    "- If it is clearly outside induction/HR-policy scope (e.g. IT passwords, building access): say it "
    "is not something the induction materials cover and point them to the right team or their manager.\n\n"
    "Do NOT state any specific policy rule, number, entitlement, or clause content. Do not invent "
    "facts. Keep it to a few sentences.\n\n"
    "Conversation so far:\n{transcript}\n\nEmployee message: {message}\n\nYour reply:"
)

VERIFIER_INSTRUCTION = (
    "You are a reviewer checking an answer for an HR induction assistant. Using ONLY the source "
    "material below, decide whether the answer is safe to send.\n\n"
    "FAIL the answer if any of these problems is present:\n"
    "- It states a fact that is not supported anywhere in the source material.\n"
    "- SCOPE VIOLATION (most important): the answer's substance is drawn from a passage marked "
    "'conditional' (for example an emergency / AIIMS / incident-response appendix) while the question "
    "describes an ordinary, non-emergency situation. If the question is about a normal working day and "
    "the answer relies on emergency or appendix content, you MUST fail it - even if the wording matches.\n"
    "- It cites a clause or document that does not appear in the source material at all.\n\n"
    "Be lenient on minor citation imprecision: if the substance is supported by a GENERAL provision, "
    "accept it even if a slightly different clause number would have been a better citation. But never "
    "be lenient about scope violations.\n\n"
    "Reply with exactly one line: 'VERDICT: pass' or 'VERDICT: fail - <short reason>'.\n\n"
    "Source material:\n{context}\n\nQuestion:\n{question}\n\nAnswer under review:\n{answer}\n\nVerdict:"
)


@dataclass
class VerifierVerdict:
    passed: bool
    reason: str


def build_llm() -> OpenAI:
    settings = get_settings()
    return OpenAI(
        model=settings.openai_chat_model, api_key=settings.openai_api_key, temperature=0
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


def generate_answer(system_prompt: str, history: list[ChatMessage], context_block: str, message: str) -> str:
    llm = build_llm()
    messages = [
        ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
        ChatMessage(role=MessageRole.SYSTEM, content=f"Source material:\n\n{context_block}"),
        *history,
        ChatMessage(role=MessageRole.USER, content=message),
    ]
    return llm.chat(messages).message.content.strip()


def verify_answer(context_block: str, question: str, answer: str) -> VerifierVerdict:
    llm = build_llm()
    prompt = VERIFIER_INSTRUCTION.format(context=context_block, question=question, answer=answer)
    verdict_text = llm.complete(prompt).text.strip()
    passed = "verdict: pass" in verdict_text.lower()
    reason = verdict_text.split("-", 1)[1].strip() if "-" in verdict_text else ""
    return VerifierVerdict(passed=passed, reason=reason)


def clarify_or_scope_response(history: list[ChatMessage], message: str) -> str:
    llm = build_llm()
    prompt = CLARIFY_INSTRUCTION.format(transcript=format_transcript(history), message=message)
    return llm.complete(prompt).text.strip()


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
