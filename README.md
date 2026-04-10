# OpenOMA Server

GraphQL server for the [OpenOMA](../openoma/) operational process framework.
It persists and exposes the full OpenOMA domain — definitions (WorkBlocks,
Flows, Contracts) and event-sourced execution tracking — through a single
`/graphql` endpoint backed by MongoDB.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  FastAPI + Strawberry GraphQL          (app.py)          │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────┐ │
│  │  Queries   │  │ Mutations  │  │  Types / Inputs    │ │
│  └─────┬──────┘  └─────┬──────┘  └────────────────────┘ │
│        │               │                                 │
│  ┌─────▼───────────────▼──────┐                          │
│  │       Services Layer       │  ← business logic,       │
│  │  work_block · flow · contract  validation, versioning │
│  │  execution · required_outcome                         │
│  └─────┬──────────────────────┘                          │
│        │                                                 │
│  ┌─────▼──────────────────────┐                          │
│  │       Store Layer          │  ← implements OpenOMA    │
│  │  DefinitionStore           │    store protocols       │
│  │  EventStore                │    over MongoDB          │
│  │  ExecutionStore            │                          │
│  └─────┬──────────────────────┘                          │
│        │                                                 │
│  ┌─────▼──────────────────────┐                          │
│  │     Models (Beanie ODM)    │  ← Mongo documents with  │
│  │  WorkBlockDoc · FlowDoc    │    bidirectional core ↔  │
│  │  ContractDoc · Execution*  │    doc conversion        │
│  └────────────────────────────┘                          │
└──────────────────────────────────────────────────────────┘
         │
         ▼
      MongoDB
```

### Layers

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **GraphQL** | `graphql/` | Schema, resolvers, input/output types. Thin — delegates to services. |
| **Services** | `services/` | Business logic, input conversion, validation, authorization hooks. |
| **Store** | `store/` | Implements OpenOMA's `DefinitionStore`, `EventStore`, and `ExecutionStore` protocols over MongoDB. |
| **Models** | `models/` | Beanie `Document` classes with indexes, versioning helpers, and `to_core()` / `from_core()` converters. |
| **Auth** | `auth/` | Middleware, context, and permission stubs (ready for JWT/OAuth integration). |

### Key design choices

- **Event-sourced execution.** Every execution state change is an immutable
  `ExecutionEvent` appended to a log. Block/Flow/Contract execution documents
  are read-side projections derived from the event stream via OpenOMA's
  `derive_*_state()` functions.
- **Immutable versioning.** Definition entities (WorkBlock, Flow, Contract,
  RequiredOutcome) are never mutated — updates create a new `(id, version)`
  document. References always pin a specific version.
- **Draft editing mode.** Canvas edits accumulate in `FlowDraftDoc` (mutable).
  An explicit "publish" validates and creates a new immutable flow version.
  Granular mutations (add/remove node, add/remove edge) avoid full-replacement overhead.
- **Separate canvas layout.** Visual positioning (node x/y, edge bend-points,
  viewport) is stored in `CanvasLayoutDoc`, keeping the OpenOMA core model pure.
- **DataLoaders & bulk queries.** N+1 loops replaced with `$or` bulk fetches.
  Strawberry DataLoaders batch field-level resolution across the query tree.
- **Real-time subscriptions.** In-process `ExecutionEventBus` publishes events
  from the execution pipeline. GraphQL subscriptions stream them over WebSocket
  (`graphql-transport-ws` protocol).
- **Protocol-based stores.** The store layer implements the abstract protocols
  defined in the `openoma` library, making it possible to swap the persistence
  backend without touching services or GraphQL.

## Tech stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12+ |
| Web framework | FastAPI |
| GraphQL | Strawberry GraphQL |
| Database | MongoDB 7 |
| ODM | Beanie + Motor (async) |
| Configuration | pydantic-settings (env vars prefixed `OPENOMA_`) |
| Packaging | uv + hatchling |
| Linting | Ruff |
| Testing | pytest + pytest-asyncio + mongomock-motor |
| Containers | Podman / Podman Compose |

## Quick start

```bash
# Install dependencies
make sync

# Start MongoDB and the server (hot-reload)
make dev
# → GraphQL Playground at http://localhost:8000/graphql
# → Health check at http://localhost:8000/health

# Or start everything in containers
make up
```

## Development

```bash
make test       # Run tests
make lint       # Ruff lint check
make fmt        # Auto-format + fix
```

### Seed data

```bash
# Populate MongoDB with sample WorkBlocks, a Flow, a Contract
uv run python scripts/seed_data.py

# Load richer example scenarios
uv run python scripts/load_scenarios.py
```

## Configuration

All settings are loaded via environment variables (prefix `OPENOMA_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENOMA_MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `OPENOMA_MONGO_DB` | `openoma` | Database name |
| `OPENOMA_SERVER_HOST` | `0.0.0.0` | Bind address |
| `OPENOMA_SERVER_PORT` | `8000` | Listen port |
| `OPENOMA_CORS_ORIGINS` | `["http://localhost:5173", "http://localhost:3000"]` | Allowed CORS origins |
| `OPENOMA_AUTH_ENABLED` | `false` | Enable authentication (stub) |
| `OPENOMA_AUTH_SECRET` | `change-me-in-production` | Auth token secret (stub) |

## Project structure

```
src/openoma_server/
├── app.py               # FastAPI application, middleware, lifespan
├── config.py            # pydantic-settings configuration
├── database.py          # Motor client + Beanie init
├── auth/                # Authentication & authorization (stubs)
│   ├── middleware.py     #   Request-level auth middleware
│   ├── context.py        #   CurrentUser model
│   └── permissions.py    #   Object-level permission checks
├── models/              # Beanie Document classes
│   ├── work_block.py     #   WorkBlockDoc
│   ├── flow.py           #   FlowDoc
│   ├── flow_draft.py     #   FlowDraftDoc (mutable canvas drafts)
│   ├── canvas_layout.py  #   CanvasLayoutDoc (visual positioning)
│   ├── contract.py       #   ContractDoc, RequiredOutcomeDoc
│   ├── execution.py      #   ExecutionEventDoc, Block/Flow/ContractExecutionDoc
│   ├── embedded.py       #   Shared embedded sub-documents
│   └── converters.py     #   Bidirectional core ↔ doc converters
├── store/               # OpenOMA store protocol implementations
│   ├── definition_store.py  # Bulk $or queries, cursor pagination
│   ├── event_store.py
│   └── execution_store.py
├── services/            # Business logic
│   ├── work_block.py
│   ├── flow.py
│   ├── flow_draft.py     #   Draft lifecycle, granular node/edge mutations
│   ├── canvas_layout.py  #   Canvas layout CRUD
│   ├── canvas.py         #   Composite canvas data queries
│   ├── contract.py
│   ├── required_outcome.py
│   ├── execution.py      #   Event-sourced execution + pub/sub hook
│   └── pubsub.py         #   In-process ExecutionEventBus
└── graphql/             # Strawberry GraphQL schema
    ├── schema.py         #   Root Query + Mutation + Subscription
    ├── context.py        #   GraphQL context (user, stores, DataLoaders)
    ├── resolvers.py      #   Doc → GQL type converters
    ├── types/            #   Output types (incl. pagination, canvas)
    ├── inputs/           #   Mutation input types (incl. filters)
    ├── queries/          #   Query resolvers (incl. canvas composites)
    ├── mutations/        #   Mutation resolvers (incl. drafts)
    └── subscriptions/    #   WebSocket subscription resolvers
tests/
├── conftest.py          # mongomock fixtures
├── test_store/          # Store layer tests
├── test_services/       # Service layer tests
└── test_graphql/        # Schema integration tests
scripts/
├── seed_data.py         # Sample data seeder
└── load_scenarios.py    # Complex scenario loader
```

## GraphQL API overview

### Queries

| Query | Description |
|-------|-------------|
| `workBlock(id, version)` | Get a WorkBlock (latest if version omitted) |
| `workBlocks(name, limit, offset)` | List WorkBlocks |
| `workBlocksConnection(first, after, filter, orderBy)` | Cursor-paginated WorkBlocks |
| `flow(id, version)` | Get a Flow |
| `flows(name, limit, offset)` | List Flows |
| `flowsConnection(first, after, filter, orderBy)` | Cursor-paginated Flows |
| `flowDraft(draftId)` | Get a mutable flow draft |
| `flowDrafts(baseFlowId, limit, offset)` | List drafts |
| `contract(id, version)` | Get a Contract |
| `contracts(name, limit, offset)` | List Contracts |
| `contractsConnection(first, after, filter, orderBy)` | Cursor-paginated Contracts |
| `requiredOutcome(id, version)` | Get a RequiredOutcome |
| `requiredOutcomes(name, limit, offset)` | List RequiredOutcomes |
| `canvasLayout(flowId, flowVersion)` | Get visual layout for a flow |
| `flowCanvas(flowId, flowVersion?)` | Composite: flow + layout + WorkBlock summaries |
| `flowExecutionCanvas(flowExecutionId)` | Composite: flow + execution + per-node states |
| `blockExecution(id)` | Get a BlockExecution |
| `blockExecutions(workBlockId, flowExecutionId, state, ...)` | List BlockExecutions |
| `flowExecution(id)` | Get a FlowExecution |
| `flowExecutions(flowId, contractExecutionId, state, ...)` | List FlowExecutions |
| `contractExecution(id)` | Get a ContractExecution |
| `contractExecutions(contractId, state, ...)` | List ContractExecutions |
| `executionEvents(executionId)` | Get event log for an execution |

### Mutations

**Definitions** — create / update for WorkBlock, Flow, Contract, RequiredOutcome.

**Draft editing** — granular canvas-friendly flow editing:

```
createFlowDraft / createBlankFlowDraft
  → addNodeToDraft · removeNodeFromDraft · updateNodeInDraft
  → addEdgeToDraft · removeEdgeToDraft
  → updateNodePositions · updateViewport
  → publishFlowDraft → new immutable FlowDoc
  → discardFlowDraft
```

**Canvas layout** — `saveCanvasLayout` / `deleteCanvasLayout`

**Execution lifecycle** — mirrors the OpenOMA event model:

```
createBlockExecution → assignExecutorToBlock → startBlockExecution
  → produceBlockOutcome → completeBlockExecution
                        → failBlockExecution
                        → cancelBlockExecution
```

Flow and Contract executions follow the same create → add children →
`refreshFlowState` / `refreshContractState` pattern.

### Subscriptions (WebSocket)

| Subscription | Description |
|-------------|-------------|
| `executionEvents(executionId?)` | Stream execution events in real time. Filter by execution ID or receive all. |

## Containers

```bash
make up       # Build & start MongoDB + server
make down     # Stop services
make mongo    # Start only MongoDB (for local dev)
make clean    # Remove containers and volumes
```

The `Containerfile` builds from the monorepo root (context `..`) so it can
copy the `openoma/` library alongside the server source.

## License

See repository root.