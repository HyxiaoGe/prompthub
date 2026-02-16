from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://prompthub:prompthub_dev@localhost:5432/prompthub"
    DATABASE_URL_SYNC: str = "postgresql://prompthub:prompthub_dev@localhost:5432/prompthub"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # App
    APP_NAME: str = "PromptHub"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_SECRET_KEY: str = "change-me-in-production"

    # API
    API_PREFIX: str = "/api/v1"
    API_DEFAULT_PAGE_SIZE: int = 20

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # LLM (Phase 5)
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str | None = None
    LLM_DEFAULT_MODEL: str = "gpt-4o-mini"
    LLM_MAX_TOKENS: int = 4096
    LLM_TEMPERATURE: float = 0.7
    LLM_TIMEOUT: int = 60
    LLM_BATCH_CONCURRENCY: int = 3

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
