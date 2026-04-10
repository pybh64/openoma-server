import asyncio
from unittest.mock import patch

import pytest
import pytest_asyncio
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient

from openoma_server.models import ALL_DOCUMENT_MODELS


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def init_test_db():
    client = AsyncMongoMockClient()
    db = client["openoma_test"]

    # mongomock doesn't support authorizedCollections/nameOnly kwargs
    original_list = db.list_collection_names

    async def patched_list(**kwargs):
        kwargs.pop("authorizedCollections", None)
        kwargs.pop("nameOnly", None)
        return await original_list(**kwargs)

    with patch.object(db, "list_collection_names", patched_list):
        await init_beanie(database=db, document_models=ALL_DOCUMENT_MODELS)

    yield db

    # Clean up all collections after each test
    for name in await db.list_collection_names():
        await db[name].drop()
    client.close()
