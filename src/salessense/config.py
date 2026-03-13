from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # API keys
    google_api_key: str
    cohere_api_key: str

    # Infrastructure
    weaviate_url: str = "http://localhost:8080"
    redis_url: str = "redis://localhost:6379"

    # Models
    llm_model: str = "gemini-2.5-flash"
    embedding_model: str = "gemini-embedding-001"
    embedding_dim: int = 3072
    rerank_model: str = "rerank-english-v3.0"

    # Retrieval
    hybrid_top_k: int = 20
    rerank_top_n: int = 5
    hybrid_alpha: float = 0.75  # 0=pure BM25, 1=pure vector

    # Cache
    redis_cache_ttl: int = 3600

    # Ingestion
    chunk_size: int = 512
    chunk_overlap: int = 64
    batch_size: int = 100

    # Eval
    eval_pass_threshold: float = 0.75

    # Weaviate collection
    weaviate_collection: str = "SalesDocument"


settings = Settings()
