"""Integration test: _append_event publishes to the event bus."""

import asyncio
from unittest.mock import patch
from uuid import uuid4

import pytest

from openoma_server.auth.context import CurrentUser
from openoma_server.services.execution import create_block_execution, start_block_execution
from openoma_server.services.pubsub import ExecutionEventBus

pytestmark = pytest.mark.asyncio

USER = CurrentUser(id="test-user", email="test@example.com")


async def test_append_event_publishes_to_bus():
    """Creating and starting a block execution should publish events to the bus."""
    test_bus = ExecutionEventBus()
    received = []

    async def subscriber():
        async for event in test_bus.subscribe(None):
            received.append(event)
            if len(received) >= 2:
                break

    task = asyncio.create_task(subscriber())
    await asyncio.sleep(0.01)

    with patch("openoma_server.services.pubsub.event_bus", test_bus):
        doc = await create_block_execution(
            work_block_id=uuid4(),
            work_block_version=1,
            node_reference_id=uuid4(),
            user=USER,
        )
        await start_block_execution(doc.execution_id)

    await asyncio.wait_for(task, timeout=2.0)

    assert len(received) == 2
    assert received[0].event_type == "created"
    assert received[1].event_type == "started"
    assert received[0].execution_id == doc.execution_id
    assert received[1].execution_id == doc.execution_id
