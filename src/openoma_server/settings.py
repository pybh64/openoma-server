"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """OpenOMA Server configuration.

    All settings can be overridden via environment variables prefixed with OPENOMA_.
    Example: OPENOMA_MONGODB_URI=mongodb://localhost:27017
    """

    model_config = {"env_prefix": "OPENOMA_"}

    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "openoma"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Auth
    auth_enabled: bool = False
    auth_backend: str = "noop"  # "noop" | "jwt" | "oauth2" (extensible)

    # Default tenant for local dev (when auth is disabled)
    default_tenant_id: str = "local"
    default_user_id: str = "local-service"


settings = Settings()
