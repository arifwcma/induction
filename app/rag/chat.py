from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.llms.openai import OpenAI

from app.config import get_settings
from app.rag.retrieval import retrieve_relevant_passages, top_passage_is_confident


DEFAULT_SYSTEM_PROMPT = (
    "You are the induction assistant for new employees at the Wimmera Catchment Management "
    "Authority (Wimmera CMA). You help them settle in by answering questions about "
    "organisational policies, procedures, the enterprise agreement, and related induction "
    "material. Answer only from the provided source passages; never invent facts.\n\n"
    "How you communicate:\n"
    "- Be concise and to the point. Never pad an answer with detail the person did not ask for.\n"
    "- Reason over the material and explain it in plain language. Do not recite long passages verbatim.\n"
    "- Use the conversation so far as context. Do not re-ask what the person has already told you.\n\n"
    "Choosing the governing rule (this is critical):\n"
    "- When several passages touch the question, decide which one actually GOVERNS the asked "
    "situation. A general clause governs unless a conditional or appendix clause's stated "
    "condition genuinely applies.\n"
    "- A passage marked as conditional (for example emergency / AIIMS incident control only) "
    "must NOT be used for an ordinary, non-emergency question. State the condition explicitly "
    "if you ever rely on such a passage.\n\n"
    "Citing sources:\n"
    "- For every substantive claim, cite the source passage it came from using its label "
    "(document name plus clause/section or page).\n"
    "- If a passage came from trainer-added knowledge, say that the information was provided by a trainer.\n\n"
    "When intent is unclear:\n"
    "- If a question is vague or ambiguous, ask one focused clarifying question to qualify what "
    "they mean, then answer precisely.\n"
    "- A bare topic with no specific question (for example just 'leave', 'pay', or 'uniform') is "
    "not specific enough. Ask which aspect they mean before answering.\n"
    "- Do not guess, do not deflect with a generic non-answer, and do not enumerate every possible "
    "interpretation in an if-this/else-that list.\n\n"
    "If a tour or general overview is requested:\n"
    "- Walk through the policies in small, bite-sized steps, one topic at a time in a few short "
    "sentences. Never dump a wall of text. End each step by inviting a specific follow-up.\n\n"
    "If the answer is not in the source passages, say so plainly and point the new employee to "
    "their manager or People & Culture. Do not extrapolate beyond the documents."
)

CONDENSE_INSTRUCTION = (
    "Given the conversation so far and a follow-up message, rewrite the follow-up as a single "
    "standalone question that can be understood without the conversation. Keep the original "
    "wording where possible. Return only the rewritten question.\n\n"
    "Conversation so far:\n{transcript}\n\nFollow-up message: {message}\n\nStandalone question:"
)

UNSURE_RESPONSE = (
    "I could not find this clearly in the induction documents, so I do not want to guess. "
    "Could you rephrase or tell me which policy or situation you mean? For anything personal "
    "or not covered by the documents, your manager or People & Culture is the right place to ask."
)


def build_llm() -> OpenAI:
    settings = get_settings()
    return OpenAI(model=settings.openai_chat_model, api_key=settings.openai_api_key)


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


def citation_label(metadata: dict) -> str:
    source = metadata.get("source", "unknown document")
    if metadata.get("origin") == "trainer":
        return f"{source} (trainer-provided)"
    if metadata.get("page") is not None:
        location = f"p.{metadata['page']}"
    elif metadata.get("section"):
        location = f"section: {metadata['section']}"
    else:
        location = ""

    label = source if not location else f"{source}, {location}"
    if metadata.get("scope") == "emergency-only":
        label += " (conditional: emergency / AIIMS incident control only)"
    return label


def format_passages_as_context(passages) -> str:
    blocks = []
    for passage in passages:
        label = citation_label(passage.node.metadata)
        blocks.append(f"[Source: {label}]\n{passage.node.get_content()}")
    return "\n\n".join(blocks)


def stream_in_pieces(text: str):
    for word in text.split(" "):
        yield word + " "


def build_message_sequence(system_prompt, history, cross_session_context, context_block, message):
    messages = [ChatMessage(role=MessageRole.SYSTEM, content=system_prompt)]
    if cross_session_context:
        messages.append(
            ChatMessage(
                role=MessageRole.SYSTEM,
                content=(
                    "Context from this employee's earlier sessions (use only if relevant; "
                    "never let it override the source passages below):\n"
                    f"{cross_session_context}"
                ),
            )
        )
    messages.append(
        ChatMessage(role=MessageRole.SYSTEM, content=f"Source passages:\n\n{context_block}")
    )
    messages.extend(history)
    messages.append(ChatMessage(role=MessageRole.USER, content=message))
    return messages


def answer_stream(
    system_prompt: str, history: list[ChatMessage], cross_session_context: str, message: str
):
    llm = build_llm()
    standalone_question = condense_to_standalone_question(llm, history, message)
    passages = retrieve_relevant_passages(standalone_question)

    if not top_passage_is_confident(passages):
        for piece in stream_in_pieces(UNSURE_RESPONSE):
            yield piece
        return

    context_block = format_passages_as_context(passages)
    messages = build_message_sequence(
        system_prompt, history, cross_session_context, context_block, message
    )

    for chunk in llm.stream_chat(messages):
        yield chunk.delta or ""


SUMMARISE_INSTRUCTION = (
    "Summarise the following conversation in two or three sentences. Capture what the employee "
    "asked about and any preferences or personal context they shared. Do not add anything that "
    "was not said.\n\nConversation:\n{transcript}\n\nSummary:"
)


def summarise_conversation(history: list[ChatMessage]) -> str:
    if not history:
        return ""
    llm = build_llm()
    prompt = SUMMARISE_INSTRUCTION.format(transcript=format_transcript(history))
    return llm.complete(prompt).text.strip()
