import qdrant_client
from llama_index.core import Settings as LlamaSettings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore

from app.config import get_settings
from app.llm_factory import make_llm


def configure_models():
    settings = get_settings()
    LlamaSettings.llm = make_llm()
    LlamaSettings.embed_model = OpenAIEmbedding(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
    )


def get_vector_store() -> QdrantVectorStore:
    settings = get_settings()
    client = qdrant_client.QdrantClient(url=settings.qdrant_url, check_compatibility=False)
    return QdrantVectorStore(
        client=client,
        collection_name=settings.qdrant_collection,
    )
