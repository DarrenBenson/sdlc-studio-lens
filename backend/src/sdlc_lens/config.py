"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "SDLC_LENS_"}

    host: str = "0.0.0.0"
    port: int = 8000
    database_url: str = "sqlite+aiosqlite:///data/db/sdlc_lens.db"
    log_level: str = "INFO"


settings = Settings()
