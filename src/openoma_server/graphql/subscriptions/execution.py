"""GraphQL subscriptions for real-time execution events."""

import asyncio
from typing import AsyncGenerator
from uuid import UUID

import strawberry

from openoma_server.graphql.types.execution import (
    ExecutionEventType,
    event_to_type,
)
from openoma_server.services.execution import subscribe_events, unsubscribe_events


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def execution_events(
        self,
        info: strawberry.Info,
        execution_id: UUID | None = None,
    ) -> AsyncGenerator[ExecutionEventType, None]:
        """Subscribe to execution events, optionally filtered by execution_id."""
        queue = subscribe_events()
        try:
            while True:
                event = await queue.get()
                if execution_id is not None and event.execution_id != execution_id:
                    continue
                yield event_to_type(event)
        except asyncio.CancelledError:
            pass
        finally:
            unsubscribe_events(queue)
