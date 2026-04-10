import asyncio
from unittest.mock import patch

import pytest
import pytest_asyncio
from beanie import init_beanie
from beanie.odm.queries.aggregation import AggregationQuery
from mongomock_motor import AsyncMongoMockClient

from openoma_server.models import ALL_DOCUMENT_MODELS

# Store original get_cursor for reference
_original_get_cursor = AggregationQuery.get_cursor


async def _patched_get_cursor(self):
    """Patch for mongomock-motor: aggregate() returns cursor directly, not a coroutine."""
    aggregation_pipeline = self.get_aggregation_pipeline()
    result = self.document_model.get_pymongo_collection().aggregate(
        aggregation_pipeline, session=self.session, **self.pymongo_kwargs
    )
    # If it's already a cursor (mongomock), return it; if awaitable, await it
    if hasattr(result, "__anext__"):
        return result
    return await result


# Apply the patch globally for tests
AggregationQuery.get_cursor = _patched_get_cursor


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
