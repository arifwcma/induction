from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Wimmera CMA Induction Chatbot"
    environment: str = "development"

    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    cohere_api_key: str = ""
    cohere_rerank_model: str = "rerank-english-v3.0"

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "induction_documents"

    documents_dir: str = "documents"

    frontend_origin: str = "http://localhost:3000"

    database_url: str = "postgresql+asyncpg://induction:induction@localhost:5432/induction"

    jwt_secret: str = ""
    cookie_secure: bool = False

    allowed_email_domain: str = "wcma.vic.gov.au"

    admin_email: str = ""
    admin_password: str = ""


def get_settings() -> Settings:
    return Settings()
