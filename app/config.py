from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Induction Assistant"
    environment: str = "development"

    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "induction_documents"

    documents_dir: str = "documents"

    frontend_origin: str = "http://localhost:3000"


def get_settings() -> Settings:
    return Settings()
