from llama_index.core import VectorStoreIndex

from app.rag.engine import configure_models, get_vector_store


def build_query_engine():
    configure_models()
    vector_store = get_vector_store()
    index = VectorStoreIndex.from_vector_store(vector_store)
    return index.as_query_engine(similarity_top_k=8)
