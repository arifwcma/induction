from llama_index.core.memory import ChatMemoryBuffer


MEMORY_TOKEN_LIMIT = 3000


_memories = {}


def get_memory(session_id: str) -> ChatMemoryBuffer:
    if session_id not in _memories:
        _memories[session_id] = ChatMemoryBuffer.from_defaults(token_limit=MEMORY_TOKEN_LIMIT)
    return _memories[session_id]
