from collections.abc import AsyncGenerator
from uuid import UUID

import strawberry

from openoma_server.graphql.resolvers import execution_event_to_gql
from openoma_server.graphql.types.execution import ExecutionEventType
from openoma_server.services.pubsub import event_bus


@strawberry.type
class ExecutionSubscription:
    @strawberry.subscription
    async def execution_events(
        self, execution_id: UUID | None = None
    ) -> AsyncGenerator[ExecutionEventType, None]:
        """Subscribe to execution events.

        Args:
            execution_id: If provided, only events for this execution.
                         If None, all execution events.
        """
        async for event_doc in event_bus.subscribe(execution_id):
            yield execution_event_to_gql(event_doc)
