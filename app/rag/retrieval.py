from dataclasses import dataclass

import cohere
from llama_index.core import VectorStoreIndex

from app.config import get_settings
from app.kb.bm25_index import load_bm25_store
from app.rag.engine import configure_models, get_vector_store


DENSE_CANDIDATES = 20
BM25_CANDIDATES = 20
PASSAGES_AFTER_RERANK = 8


_index = None
_cohere_client = None
_bm25_store = None


@dataclass
class Passage:
    text_for_index: str
    raw_text: str
    metadata: dict
    score: float = 0.0


def get_index() -> VectorStoreIndex:
    global _index
    if _index is None:
        configure_models()
        _index = VectorStoreIndex.from_vector_store(get_vector_store())
    return _index


def get_cohere_client() -> cohere.Client:
    global _cohere_client
    if _cohere_client is None:
        _cohere_client = cohere.Client(api_key=get_settings().cohere_api_key)
    return _cohere_client


def get_bm25():
    global _bm25_store
    if _bm25_store is None:
        _bm25_store = load_bm25_store()
    return _bm25_store


def dense_candidates(question: str) -> list[Passage]:
    nodes = get_index().as_retriever(similarity_top_k=DENSE_CANDIDATES).retrieve(question)
    passages = []
    for node in nodes:
        metadata = dict(node.node.metadata)
        passages.append(
            Passage(
                text_for_index=node.node.get_content(),
                raw_text=metadata.get("raw_text", node.node.get_content()),
                metadata=metadata,
            )
        )
    return passages


def bm25_candidates(question: str) -> list[Passage]:
    store = get_bm25()
    if store is None:
        return []
    passages = []
    for record in store.search(question, BM25_CANDIDATES):
        passages.append(
            Passage(
                text_for_index=record["text_for_index"],
                raw_text=record["raw_text"],
                metadata=record["metadata"],
            )
        )
    return passages


def dedup_key(passage: Passage) -> tuple:
    return (passage.metadata.get("clause_number", ""), passage.raw_text[:120])


def fuse_candidates(dense: list[Passage], lexical: list[Passage]) -> list[Passage]:
    fused = {}
    for passage in dense + lexical:
        fused.setdefault(dedup_key(passage), passage)
    return list(fused.values())


def rerank(question: str, candidates: list[Passage]) -> list[Passage]:
    if not candidates:
        return []
    documents = [passage.text_for_index for passage in candidates]
    response = get_cohere_client().rerank(
        model=get_settings().cohere_rerank_model,
        query=question,
        documents=documents,
        top_n=min(PASSAGES_AFTER_RERANK, len(documents)),
    )
    reranked = []
    for result in response.results:
        passage = candidates[result.index]
        passage.score = result.relevance_score
        reranked.append(passage)
    return reranked


def gather_candidates(queries: list[str]) -> list[Passage]:
    fused: dict[tuple, Passage] = {}
    for query in queries:
        for passage in dense_candidates(query) + bm25_candidates(query):
            fused.setdefault(dedup_key(passage), passage)
    return list(fused.values())


def retrieve_relevant_passages(question: str, extra_queries: list[str] = ()) -> list[Passage]:
    queries = [question, *extra_queries]
    candidates = gather_candidates(queries)
    return rerank(question, candidates)
