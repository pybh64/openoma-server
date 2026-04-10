"""Tests for the in-process async event bus."""

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from openoma_server.models.execution import ExecutionEventDoc
from openoma_server.services.pubsub import ExecutionEventBus


def _make_event_doc(execution_id=None, event_type="STARTED"):
    return ExecutionEventDoc(
        event_id=uuid4(),
        timestamp=datetime.now(UTC),
        execution_id=execution_id or uuid4(),
        event_type=event_type,
    )


pytestmark = pytest.mark.asyncio


async def test_subscribe_to_specific_execution():
    bus = ExecutionEventBus()
    exec_id = uuid4()
    received = []

    async def subscriber():
        async for event in bus.subscribe(exec_id):
            received.append(event)
            if len(received) >= 2:
                break

    task = asyncio.create_task(subscriber())
    await asyncio.sleep(0.01)

    e1 = _make_event_doc(exec_id, "STARTED")
    e2 = _make_event_doc(uuid4(), "STARTED")  # Different execution — filtered
    e3 = _make_event_doc(exec_id, "COMPLETED")

    await bus.publish(e1)
    await bus.publish(e2)
    await bus.publish(e3)

    await asyncio.wait_for(task, timeout=2.0)
    assert len(received) == 2
    assert received[0].event_id == e1.event_id
    assert received[1].event_id == e3.event_id


async def test_subscribe_to_all_events():
    bus = ExecutionEventBus()
    received = []

    async def subscriber():
        async for event in bus.subscribe(None):
            received.append(event)
            if len(received) >= 3:
                break

    task = asyncio.create_task(subscriber())
    await asyncio.sleep(0.01)

    e1 = _make_event_doc()
    e2 = _make_event_doc()
    e3 = _make_event_doc()

    await bus.publish(e1)
    await bus.publish(e2)
    await bus.publish(e3)

    await asyncio.wait_for(task, timeout=2.0)
    assert len(received) == 3


async def test_subscriber_cleanup_on_cancel():
    bus = ExecutionEventBus()
    exec_id = uuid4()

    async def subscriber():
        async for _ in bus.subscribe(exec_id):
            pass

    task = asyncio.create_task(subscriber())
    await asyncio.sleep(0.01)

    assert len(bus._subscribers[exec_id]) == 1

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert exec_id not in bus._subscribers or len(bus._subscribers[exec_id]) == 0


async def test_multiple_subscribers():
    bus = ExecutionEventBus()
    exec_id = uuid4()
    received1 = []
    received2 = []

    async def sub1():
        async for event in bus.subscribe(exec_id):
            received1.append(event)
            if len(received1) >= 1:
                break

    async def sub2():
        async for event in bus.subscribe(exec_id):
            received2.append(event)
            if len(received2) >= 1:
                break

    t1 = asyncio.create_task(sub1())
    t2 = asyncio.create_task(sub2())
    await asyncio.sleep(0.01)

    e = _make_event_doc(exec_id)
    await bus.publish(e)

    await asyncio.wait_for(asyncio.gather(t1, t2), timeout=2.0)
    assert len(received1) == 1
    assert len(received2) == 1
