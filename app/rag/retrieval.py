from llama_index.core import VectorStoreIndex
from llama_index.postprocessor.cohere_rerank import CohereRerank

from app.config import get_settings
from app.rag.engine import configure_models, get_vector_store


CANDIDATES_BEFORE_RERANK = 20
PASSAGES_AFTER_RERANK = 8
RELEVANCE_FLOOR = 0.30


_index = None
_reranker = None


def get_index() -> VectorStoreIndex:
    global _index
    if _index is None:
        configure_models()
        _index = VectorStoreIndex.from_vector_store(get_vector_store())
    return _index


def get_reranker() -> CohereRerank:
    global _reranker
    if _reranker is None:
        settings = get_settings()
        _reranker = CohereRerank(
            api_key=settings.cohere_api_key,
            model=settings.cohere_rerank_model,
            top_n=PASSAGES_AFTER_RERANK,
        )
    return _reranker


def retrieve_relevant_passages(question: str):
    retriever = get_index().as_retriever(similarity_top_k=CANDIDATES_BEFORE_RERANK)
    candidate_passages = retriever.retrieve(question)
    if not candidate_passages:
        return []
    reranked_passages = get_reranker().postprocess_nodes(
        candidate_passages,
        query_str=question,
    )
    return reranked_passages


def top_passage_is_confident(passages) -> bool:
    if not passages:
        return False
    return passages[0].score is not None and passages[0].score >= RELEVANCE_FLOOR
