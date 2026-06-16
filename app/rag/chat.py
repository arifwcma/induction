from llama_index.core import VectorStoreIndex

from app.rag.engine import configure_models, get_vector_store


SYSTEM_PROMPT = (
    "You are the assistant for the Wimmera Regional Catchment Strategy (RCS). "
    "Answer only from the provided RCS documents and keep replies short and to the point. "
    "If the question is vague, ambiguous, or not confidently covered by the documents, "
    "ask one concise clarifying question instead of guessing or giving a generic answer. "
    "Do not invent facts and do not pad the answer with unrelated detail."
)

RETRIEVED_CHUNKS = 8


_index = None


def get_index() -> VectorStoreIndex:
    global _index
    if _index is None:
        configure_models()
        _index = VectorStoreIndex.from_vector_store(get_vector_store())
    return _index


def build_chat_engine(memory):
    index = get_index()
    return index.as_chat_engine(
        chat_mode="condense_plus_context",
        memory=memory,
        system_prompt=SYSTEM_PROMPT,
        similarity_top_k=RETRIEVED_CHUNKS,
    )
