"""Application settings loaded from .env / environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ollama_base_url: str = "http://localhost:11434"
    ollama_primary_model: str = "qwen2.5:7b-instruct-q4_K_M"
    ollama_fallback_model: str = "llama3.1:8b-instruct-q4_K_M"
    ollama_timeout_seconds: float = 120.0

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    log_level: str = "info"


settings = Settings()
