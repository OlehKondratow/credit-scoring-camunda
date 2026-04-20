"""Application configuration. User-facing strings are Polish; code/docs English."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Data residency: Warsaw region (Vertex AI, GCS).
    google_cloud_project: str = ""
    google_cloud_region: str = "europe-central2"

    embedding_model: str = "text-embedding-004"
    llm_model: str = "gemini-1.5-pro"

    use_mock_vector_db: bool = True
    use_mock_llm: bool = True
    mock_vector_top_k: int = 5

    # Matching Engine / Vector Search (when not mock)
    vector_index_endpoint_id: str = ""
    vector_deployed_index_id: str = ""
    vector_index_id: str = ""
    gcs_embeddings_uri: str = ""

    log_level: str = "INFO"

    # BIK mock latency simulation (seconds)
    bik_mock_delay_s: float = 0.05


@lru_cache
def get_settings() -> Settings:
    return Settings()
