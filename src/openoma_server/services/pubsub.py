"""In-process async pub/sub for execution events.

Subscribers receive events for specific execution_ids or for all events.
Uses asyncio.Queue per subscriber for backpressure.
"""

import asyncio
import contextlib
from collections import defaultdict
from uuid import UUID

from openoma_server.models.execution import ExecutionEventDoc


class ExecutionEventBus:
    def __init__(self):
        self._subscribers: dict[UUID | None, list[asyncio.Queue]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def publish(self, event_doc: ExecutionEventDoc):
        """Publish an event. Called from _append_event."""
        async with self._lock:
            for queue in self._subscribers.get(event_doc.execution_id, []):
                with contextlib.suppress(asyncio.QueueFull):
                    queue.put_nowait(event_doc)

            for queue in self._subscribers.get(None, []):
                with contextlib.suppress(asyncio.QueueFull):
                    queue.put_nowait(event_doc)

    async def subscribe(self, execution_id: UUID | None = None, max_queue: int = 100):
        """Subscribe to events. Yields ExecutionEventDoc instances.

        Args:
            execution_id: If provided, only receive events for this execution.
                         If None, receive all events.
            max_queue: Max queue size before dropping events.
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue)
        async with self._lock:
            self._subscribers[execution_id].append(queue)
        try:
            while True:
                event_doc = await queue.get()
                yield event_doc
        finally:
            async with self._lock:
                self._subscribers[execution_id].remove(queue)
                if not self._subscribers[execution_id]:
                    del self._subscribers[execution_id]


# Global singleton
event_bus = ExecutionEventBus()
