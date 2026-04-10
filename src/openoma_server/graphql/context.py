from dataclasses import dataclass, field

from starlette.requests import Request

from openoma_server.auth.context import CurrentUser
from openoma_server.store.definition_store import MongoDefinitionStore
from openoma_server.store.event_store import MongoEventStore
from openoma_server.store.execution_store import MongoExecutionStore

# Singleton store instances
_definition_store = MongoDefinitionStore()
_event_store = MongoEventStore()
_execution_store = MongoExecutionStore()


@dataclass
class GraphQLContext:
    request: Request
    user: CurrentUser
    definition_store: MongoDefinitionStore = field(default_factory=lambda: _definition_store)
    event_store: MongoEventStore = field(default_factory=lambda: _event_store)
    execution_store: MongoExecutionStore = field(default_factory=lambda: _execution_store)


async def get_context(request: Request) -> GraphQLContext:
    user = getattr(request.state, "user", CurrentUser())
    return GraphQLContext(request=request, user=user)
