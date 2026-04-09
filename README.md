# openoma-server

A GraphQL server for the [OpenOMA](https://github.com/your-org/openoma) operational process framework.

Built with **Strawberry GraphQL**, **FastAPI**, **Beanie ODM**, and **MongoDB**.

## Features

- Full CRUD for core entities — WorkBlock, Flow, Contract
- Execution lifecycle management with event-sourced state
- Real-time WebSocket subscriptions for execution events
- Pluggable authentication (bypassable for local development)
- ABAC authorization with decoupled policy engine
- Multi-tenant data isolation
- MongoDB persistence via Beanie ODM

## Quick Start

### Prerequisites

- Python 3.13+
- [UV](https://docs.astral.sh/uv/) package manager
- [Podman](https://podman.io/) (for local MongoDB) or a running MongoDB instance

### Setup

```bash
# Clone and install
git clone <repo-url>
cd openoma-server
uv sync

# Start MongoDB via Podman
make db-up

# Run the server
make run
```

The GraphQL playground is available at [http://localhost:8000/graphql](http://localhost:8000/graphql).

### Configuration

All settings use the `OPENOMA_` environment variable prefix:

| Variable | Default | Description |
|---|---|---|
| `OPENOMA_MONGODB_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `OPENOMA_MONGODB_DB_NAME` | `openoma` | Database name |
| `OPENOMA_HOST` | `0.0.0.0` | Server bind host |
| `OPENOMA_PORT` | `8000` | Server bind port |
| `OPENOMA_DEBUG` | `false` | Enable debug mode (auto-reload) |
| `OPENOMA_AUTH_ENABLED` | `false` | Enable authentication |
| `OPENOMA_AUTH_BACKEND` | `noop` | Auth backend (`noop`, `jwt`, `oauth2`) |
| `OPENOMA_DEFAULT_TENANT_ID` | `local` | Default tenant when auth is disabled |
| `OPENOMA_DEFAULT_USER_ID` | `local-service` | Default user when auth is disabled |

### Running Tests

```bash
# All tests (uses in-memory mongomock — no MongoDB required)
make test

# With verbose output
make test-v
```

## Architecture

```
src/openoma_server/
├── app.py                # FastAPI application factory
├── settings.py           # Environment-based configuration
├── db/                   # Database layer (Beanie documents)
│   ├── connection.py     # MongoDB connection lifecycle
│   └── models/           # Beanie document models
├── graphql/              # GraphQL schema layer
│   ├── schema.py         # Root schema (Query, Mutation, Subscription)
│   ├── types/            # Strawberry type definitions
│   ├── inputs/           # Strawberry input types
│   ├── queries/          # Query resolvers
│   ├── mutations/        # Mutation resolvers
│   └── subscriptions/    # Subscription resolvers
├── auth/                 # Pluggable auth system
│   ├── backend.py        # AuthBackend protocol + NoOpAuthBackend
│   ├── policies.py       # ABAC policy engine
│   ├── permissions.py    # Strawberry permission classes
│   └── middleware.py     # FastAPI auth middleware
└── services/             # Business logic layer
    ├── work_block.py     # WorkBlock CRUD + versioning
    ├── flow.py           # Flow CRUD + validation
    ├── contract.py       # Contract CRUD + validation
    ├── execution.py      # Execution lifecycle
    └── event_store.py    # MongoDB-backed EventStore
```

### Auth Plugin System

Authentication uses a protocol-based plugin system:

```python
from openoma_server.auth import AuthBackend, AuthContext, register_auth_backend

class MyJWTBackend:
    async def authenticate(self, request) -> AuthContext | None:
        token = request.headers.get("Authorization")
        # ... validate token, return AuthContext
        return AuthContext(user_id="...", tenant_id="...", attributes={...})

register_auth_backend(MyJWTBackend())
```

Set `OPENOMA_AUTH_ENABLED=false` (default) to bypass authentication during development.

### Authorization

Uses Attribute-Based Access Control (ABAC), completely decoupled from domain models:

```python
from openoma_server.auth.policies import PolicyEngine, Policy

engine = PolicyEngine()
engine.add_policy(Policy(
    name="managers-can-delete",
    action="delete",
    resource="*",
    condition=lambda ctx: "manager" in ctx.attributes.get("roles", []),
))
```

## Development

```bash
make help          # Show all available commands
make run           # Start the server
make dev           # Start with auto-reload
make test          # Run tests
make lint          # Run linter
make db-up         # Start MongoDB via Podman
make db-down       # Stop MongoDB
```

## License

See [LICENSE](LICENSE).
