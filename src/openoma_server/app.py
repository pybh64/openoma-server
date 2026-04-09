"""FastAPI application factory with Strawberry GraphQL integration."""

from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request
from strawberry.fastapi import GraphQLRouter

from openoma_server.auth.backend import get_auth_backend
from openoma_server.auth.middleware import AuthMiddleware
from openoma_server.auth.policies import create_default_policy_engine
from openoma_server.db.connection import close_db, connect_db
from openoma_server.graphql.schema import schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()


def _default_context_getter(request: Request) -> dict:
    """Build the Strawberry context dict from the request.

    Note: Strawberry merges this with default context (request, background_tasks, response).
    We add auth and policy_engine from middleware/app state.
    """
    auth = getattr(request.state, "auth", None)
    policy_engine = getattr(request.app.state, "policy_engine", None)
    return {
        "auth": auth,
        "policy_engine": policy_engine,
    }


def create_app(
    *,
    context_getter: Callable | None = None,
    skip_lifespan: bool = False,
) -> FastAPI:
    app = FastAPI(
        title="OpenOMA Server",
        description="GraphQL server for the OpenOMA operational process framework",
        version="0.1.0",
        lifespan=None if skip_lifespan else lifespan,
    )

    # Auth middleware
    backend = get_auth_backend()
    app.add_middleware(AuthMiddleware, backend=backend)

    # ABAC policy engine
    app.state.policy_engine = create_default_policy_engine()

    # GraphQL endpoint
    graphql_app = GraphQLRouter(
        schema,
        context_getter=context_getter or _default_context_getter,
    )
    app.include_router(graphql_app, prefix="/graphql")

    # Health check
    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app
