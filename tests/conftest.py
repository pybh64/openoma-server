"""Shared test fixtures for OpenOMA Server tests."""

import asyncio

import pytest
import pytest_asyncio
from beanie import init_beanie
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

from openoma_server.auth.context import AuthContext
from openoma_server.auth.policies import create_default_policy_engine
from openoma_server.db.models import ALL_DOCUMENT_MODELS


def _patch_mongomock_list_collection_names():
    """Patch mongomock to accept keyword args that newer PyMongo/Beanie pass."""
    import mongomock.database as mdb

    _original = mdb.Database.list_collection_names

    def _patched(self, *args, **kwargs):
        kwargs.pop("authorizedCollections", None)
        kwargs.pop("nameOnly", None)
        return _original(self, *args, **kwargs)

    mdb.Database.list_collection_names = _patched


_patch_mongomock_list_collection_names()


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def mongo_client():
    """In-memory MongoDB client for testing."""
    client = AsyncMongoMockClient()
    yield client


@pytest_asyncio.fixture
async def init_db(mongo_client):
    """Initialize Beanie with mongomock for testing."""
    db = mongo_client["openoma_test"]
    await init_beanie(database=db, document_models=ALL_DOCUMENT_MODELS)
    yield db
    # Clean up all collections after each test
    for name in await db.list_collection_names():
        await db.drop_collection(name)


@pytest.fixture
def auth_context() -> AuthContext:
    """Default test auth context."""
    return AuthContext(
        user_id="test-user",
        tenant_id="test-tenant",
        attributes={"type": "service", "roles": ["admin"]},
    )


@pytest.fixture
def policy_engine():
    return create_default_policy_engine()


@pytest_asyncio.fixture
async def test_client(init_db, auth_context, policy_engine):
    """FastAPI test client with mocked DB and auth."""
    from openoma_server.app import create_app

    def get_test_context():
        return {
            "auth": auth_context,
            "policy_engine": policy_engine,
        }

    app = create_app(context_getter=get_test_context, skip_lifespan=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
