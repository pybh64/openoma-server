from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from openoma_server.auth.middleware import AuthMiddleware
from openoma_server.config import settings
from openoma_server.database import close_db, init_db
from openoma_server.graphql.context import get_context
from openoma_server.graphql.schema import schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="OpenOMA Server",
    description="GraphQL server for the OpenOMA operational process framework",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth middleware (stub — passes all requests through)
app.add_middleware(AuthMiddleware)

# GraphQL
graphql_router = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_router, prefix="/graphql")


@app.get("/health")
async def health():
    return {"status": "ok"}
