from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Wimmera CMA Induction Chatbot"
    environment: str = "development"

    llm_provider: str = "openai"
    fast_llm_provider: str = "openai"
    # gpt-5.4-mini: OpenAI's strongest mini model, chosen for quality on the
    # mechanical steps (applicability/verify judgements). Supports seed for
    # deterministic retrieval and, unlike gpt-4o-mini, has no 10k-requests/day
    # Tier-1 cap (GPT-5 models are RPM/TPM-limited only).
    fast_chat_model: str = "gpt-5.4-mini"

    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    anthropic_api_key: str = ""
    anthropic_chat_model: str = "claude-opus-4-8"

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
