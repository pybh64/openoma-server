"""Tests for MongoEventStore."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from openoma.execution.events import ExecutionEvent, ExecutionEventType

from openoma_server.store.event_store import MongoEventStore


@pytest.fixture
def store():
    return MongoEventStore()


def _make_event(
    execution_id=None,
    event_type=ExecutionEventType.CREATED,
    ts_offset_seconds=0,
):
    return ExecutionEvent(
        id=uuid4(),
        timestamp=datetime.now(UTC) + timedelta(seconds=ts_offset_seconds),
        execution_id=execution_id or uuid4(),
        event_type=event_type,
    )


class TestEventStore:
    @pytest.mark.asyncio
    async def test_append_and_get_events(self, store):
        eid = uuid4()
        e1 = _make_event(execution_id=eid, event_type=ExecutionEventType.CREATED)
        e2 = _make_event(
            execution_id=eid,
            event_type=ExecutionEventType.STARTED,
            ts_offset_seconds=1,
        )
        await store.append(e1)
        await store.append(e2)

        events = await store.get_events(eid)
        assert len(events) == 2
        assert events[0].event_type == ExecutionEventType.CREATED
        assert events[1].event_type == ExecutionEventType.STARTED

    @pytest.mark.asyncio
    async def test_get_events_with_after_filter(self, store):
        eid = uuid4()
        now = datetime.now(UTC)
        e1 = _make_event(execution_id=eid, event_type=ExecutionEventType.CREATED)
        e2 = _make_event(
            execution_id=eid,
            event_type=ExecutionEventType.STARTED,
            ts_offset_seconds=10,
        )
        await store.append(e1)
        await store.append(e2)

        events = await store.get_events(eid, after=now + timedelta(seconds=5))
        assert len(events) == 1
        assert events[0].event_type == ExecutionEventType.STARTED

    @pytest.mark.asyncio
    async def test_get_latest_event(self, store):
        eid = uuid4()
        await store.append(
            _make_event(execution_id=eid, event_type=ExecutionEventType.CREATED)
        )
        await store.append(
            _make_event(
                execution_id=eid,
                event_type=ExecutionEventType.COMPLETED,
                ts_offset_seconds=5,
            )
        )

        latest = await store.get_latest_event(eid)
        assert latest is not None
        assert latest.event_type == ExecutionEventType.COMPLETED

    @pytest.mark.asyncio
    async def test_get_latest_event_none(self, store):
        result = await store.get_latest_event(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_latest_events_batch(self, store):
        eid1, eid2 = uuid4(), uuid4()
        await store.append(_make_event(execution_id=eid1, event_type=ExecutionEventType.CREATED))
        await store.append(
            _make_event(
                execution_id=eid1,
                event_type=ExecutionEventType.STARTED,
                ts_offset_seconds=1,
            )
        )
        await store.append(_make_event(execution_id=eid2, event_type=ExecutionEventType.CREATED))

        results = await store.get_latest_events([eid1, eid2])
        assert len(results) == 2
        types = {e.event_type for e in results}
        assert ExecutionEventType.STARTED in types
        assert ExecutionEventType.CREATED in types

    @pytest.mark.asyncio
    async def test_events_isolated_by_execution_id(self, store):
        eid1, eid2 = uuid4(), uuid4()
        await store.append(_make_event(execution_id=eid1))
        await store.append(_make_event(execution_id=eid2))

        events1 = await store.get_events(eid1)
        assert len(events1) == 1
