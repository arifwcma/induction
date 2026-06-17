import json
import re
from pathlib import Path

from rank_bm25 import BM25Okapi


BM25_CORPUS_PATH = Path("kb_index/bm25_corpus.json")
TOKEN = re.compile(r"[a-z0-9]+(?:\.[0-9]+)*")


def tokenize(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


def save_corpus(records: list[dict]):
    BM25_CORPUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    BM25_CORPUS_PATH.write_text(json.dumps(records), encoding="utf-8")


class BM25Store:
    def __init__(self, records: list[dict]):
        self.records = records
        self.engine = BM25Okapi([tokenize(record["text_for_index"]) for record in records])

    def search(self, query: str, top_k: int) -> list[dict]:
        scores = self.engine.get_scores(tokenize(query))
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [self.records[index] for index in ranked_indices[:top_k]]


def load_bm25_store() -> BM25Store | None:
    if not BM25_CORPUS_PATH.exists():
        return None
    records = json.loads(BM25_CORPUS_PATH.read_text(encoding="utf-8"))
    if not records:
        return None
    return BM25Store(records)
