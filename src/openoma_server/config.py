from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "openoma"

    server_host: str = "0.0.0.0"
    server_port: int = 8000

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Auth settings (stubs — will be replaced when auth is implemented)
    auth_enabled: bool = False
    auth_secret: str = "change-me-in-production"

    model_config = {"env_prefix": "OPENOMA_"}


settings = Settings()
