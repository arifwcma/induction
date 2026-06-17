import sys

from llama_index.core.memory import ChatMemoryBuffer

from app.rag.chat import answer_stream


def ask_cli():
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        print('Usage: python -m app.ask "your question"')
        return

    memory = ChatMemoryBuffer.from_defaults()
    for piece in answer_stream(memory, question):
        print(piece, end="", flush=True)
    print()


if __name__ == "__main__":
    ask_cli()
