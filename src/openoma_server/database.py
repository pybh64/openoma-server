from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from openoma_server.config import settings

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongo_uri)
    return _client


async def init_db() -> None:
    from openoma_server.models import ALL_DOCUMENT_MODELS

    client = get_client()
    await init_beanie(
        database=client[settings.mongo_db],
        document_models=ALL_DOCUMENT_MODELS,
    )


async def close_db() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
