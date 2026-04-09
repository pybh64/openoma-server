"""MongoDB connection lifecycle management."""

from beanie import init_beanie
from pymongo import AsyncMongoClient

from openoma_server.settings import settings

_client: AsyncMongoClient | None = None


async def connect_db() -> None:
    """Initialize MongoDB connection and Beanie ODM."""
    global _client

    from openoma_server.db.models import ALL_DOCUMENT_MODELS

    _client = AsyncMongoClient(settings.mongodb_uri)
    database = _client[settings.mongodb_db_name]
    await init_beanie(database=database, document_models=ALL_DOCUMENT_MODELS)


async def close_db() -> None:
    """Close MongoDB connection."""
    global _client
    if _client is not None:
        _client.close()
        _client = None


def get_client() -> AsyncMongoClient | None:
    return _client
