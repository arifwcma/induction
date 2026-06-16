import sys

from app.rag.query import build_query_engine


def ask_cli():
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        print('Usage: python -m app.ask "your question"')
        return

    query_engine = build_query_engine()
    response = query_engine.query(question)
    print(response)


if __name__ == "__main__":
    ask_cli()
