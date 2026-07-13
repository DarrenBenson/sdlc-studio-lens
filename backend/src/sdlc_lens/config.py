"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "SDLC_LENS_"}

    host: str = "0.0.0.0"
    port: int = 8000
    database_url: str = "sqlite+aiosqlite:///data/db/sdlc_lens.db"
    log_level: str = "INFO"
    # Optional allowlist base for local project sdlc_path values. When set, any
    # local sdlc_path must resolve to a location within this directory. When
    # None (default), no restriction is applied (backward compatible).
    allowed_project_base: str | None = None
    # Optional urlsafe base64 Fernet key for encrypting stored access tokens at
    # rest (env SDLC_LENS_TOKEN_ENCRYPTION_KEY). When set, GitHub PATs are
    # encrypted in the database and transparently decrypted for API calls. When
    # None (default), tokens are stored as plaintext (opt-in, backward compatible).
    token_encryption_key: str | None = None
    # Seconds between background freshness polls of auto-sync projects. Set to 0 to
    # DISABLE the poller entirely - no task is created at all, rather than one that idles
    # (env SDLC_LENS_SYNC_POLL_INTERVAL_SECONDS).
    sync_poll_interval_seconds: int = 300
    # Ceiling on the exponential backoff applied to a project that keeps failing its poll,
    # so an expired token cannot have us hammering GitHub every tick for ever.
    sync_poll_max_backoff_seconds: int = 3600


settings = Settings()
