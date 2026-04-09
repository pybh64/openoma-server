"""MongoDB-backed implementation of the openoma EventStore protocol."""

from datetime import datetime
from uuid import UUID

from openoma import ExecutionEvent, ExecutionEventType, ExecutorInfo

from openoma_server.db.models import ExecutionEventDocument


class MongoEventStore:
    """Async MongoDB-backed EventStore.

    Implements the same contract as openoma.store.EventStore but uses
    async MongoDB operations via Beanie.
    """

    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id

    async def append(self, event: ExecutionEvent) -> None:
        """Append an immutable event to the store."""
        doc = ExecutionEventDocument(
            event_id=event.id,
            timestamp=event.timestamp,
            execution_id=event.execution_id,
            event_type=event.event_type.value,
            executor=event.executor.model_dump() if event.executor else None,
            payload=event.payload,
            metadata=event.metadata,
            tenant_id=self.tenant_id,
        )
        await doc.insert()

    async def get_events(
        self,
        execution_id: UUID,
        after: datetime | None = None,
    ) -> list[ExecutionEvent]:
        """Retrieve events for an execution, optionally after a timestamp."""
        query: dict = {
            "execution_id": execution_id,
            "tenant_id": self.tenant_id,
        }
        if after is not None:
            query["timestamp"] = {"$gt": after}

        docs = await ExecutionEventDocument.find(
            query, sort=[("timestamp", 1)]
        ).to_list()
        return [_doc_to_event(d) for d in docs]

    async def get_latest_event(self, execution_id: UUID) -> ExecutionEvent | None:
        """Retrieve the most recent event for an execution."""
        doc = await ExecutionEventDocument.find_one(
            {"execution_id": execution_id, "tenant_id": self.tenant_id},
            sort=[("timestamp", -1)],
        )
        if doc is None:
            return None
        return _doc_to_event(doc)


def _doc_to_event(doc: ExecutionEventDocument) -> ExecutionEvent:
    executor = None
    if doc.executor:
        executor = ExecutorInfo(**doc.executor)
    return ExecutionEvent(
        id=doc.event_id,
        timestamp=doc.timestamp,
        execution_id=doc.execution_id,
        event_type=ExecutionEventType(doc.event_type),
        executor=executor,
        payload=doc.payload,
        metadata=doc.metadata,
    )
