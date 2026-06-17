import sys

from app.rag.chat import answer_stream


def ask_cli():
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        print('Usage: python -m app.ask "your question"')
        return

    for piece in answer_stream([], "", question):
        print(piece, end="", flush=True)
    print()


if __name__ == "__main__":
    ask_cli()
