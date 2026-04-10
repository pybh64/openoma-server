"""MongoDB implementation of the openoma EventStore protocol."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from openoma.execution.events import ExecutionEvent

from openoma_server.models.execution import ExecutionEventDoc


class MongoEventStore:
    """MongoDB-backed EventStore implementing the openoma protocol."""

    async def append(self, event: ExecutionEvent) -> None:
        doc = ExecutionEventDoc.from_core(event)
        await doc.insert()

    async def get_events(
        self,
        execution_id: UUID,
        after: datetime | None = None,
    ) -> list[ExecutionEvent]:
        filters = [ExecutionEventDoc.execution_id == execution_id]
        if after is not None:
            filters.append(ExecutionEventDoc.timestamp > after)

        docs = await ExecutionEventDoc.find(*filters).sort("+timestamp").to_list()
        return [d.to_core() for d in docs]

    async def get_latest_event(self, execution_id: UUID) -> ExecutionEvent | None:
        doc = await ExecutionEventDoc.find_one(
            ExecutionEventDoc.execution_id == execution_id,
            sort=[("timestamp", -1)],
        )
        return doc.to_core() if doc else None

    async def get_latest_events(self, execution_ids: list[UUID]) -> list[ExecutionEvent]:
        if not execution_ids:
            return []
        docs = (
            await ExecutionEventDoc.find({"execution_id": {"$in": execution_ids}})
            .sort(-ExecutionEventDoc.timestamp)
            .to_list()
        )
        seen: set[UUID] = set()
        results: list[ExecutionEvent] = []
        for doc in docs:
            if doc.execution_id not in seen:
                seen.add(doc.execution_id)
                results.append(doc.to_core())
        return results
