"""Service layer for execution lifecycle operations."""

import asyncio
from datetime import datetime
from uuid import UUID, uuid4

from openoma import (
    BlockExecution,
    ContractExecution,
    ExecutionEvent,
    ExecutionEventType,
    ExecutorInfo,
    FlowExecution,
)

from openoma_server.auth.context import AuthContext
from openoma_server.db.models import (
    BlockExecutionDocument,
    ContractExecutionDocument,
    FlowExecutionDocument,
)
from openoma_server.services.event_store import MongoEventStore

# In-process event bus for subscriptions
_event_listeners: list[asyncio.Queue] = []


def subscribe_events() -> asyncio.Queue:
    """Subscribe to execution events. Returns a queue that receives new events."""
    queue: asyncio.Queue = asyncio.Queue()
    _event_listeners.append(queue)
    return queue


def unsubscribe_events(queue: asyncio.Queue) -> None:
    """Remove an event subscription."""
    if queue in _event_listeners:
        _event_listeners.remove(queue)


async def _broadcast_event(event: ExecutionEvent) -> None:
    """Push event to all subscribed listeners."""
    for queue in _event_listeners:
        await queue.put(event)


async def start_block_execution(
    *,
    node_reference_id: UUID,
    work_block_id: UUID,
    work_block_version: int,
    flow_execution_id: UUID | None = None,
    executor_type: str = "system",
    executor_id: str = "",
    auth: AuthContext,
) -> BlockExecution:
    """Create a new BlockExecution and emit a CREATED event."""
    execution_id = uuid4()
    store = MongoEventStore(tenant_id=auth.tenant_id)

    executor = ExecutorInfo(
        type=executor_type,
        identifier=executor_id or auth.user_id,
    )

    created_event = ExecutionEvent(
        execution_id=execution_id,
        event_type=ExecutionEventType.CREATED,
        executor=executor,
    )
    await store.append(created_event)
    await _broadcast_event(created_event)

    doc = BlockExecutionDocument(
        execution_id=execution_id,
        node_reference_id=node_reference_id,
        work_block_id=work_block_id,
        work_block_version=work_block_version,
        flow_execution_id=flow_execution_id,
        tenant_id=auth.tenant_id,
    )
    await doc.insert()

    return BlockExecution(
        id=execution_id,
        node_reference_id=node_reference_id,
        work_block_id=work_block_id,
        work_block_version=work_block_version,
        events=[created_event],
    )


async def emit_execution_event(
    *,
    execution_id: UUID,
    event_type: str,
    executor_type: str | None = None,
    executor_id: str | None = None,
    payload: any = None,
    metadata: dict | None = None,
    auth: AuthContext,
) -> ExecutionEvent:
    """Emit a new event for an existing execution."""
    store = MongoEventStore(tenant_id=auth.tenant_id)

    executor = None
    if executor_type and executor_id:
        executor = ExecutorInfo(type=executor_type, identifier=executor_id)

    event = ExecutionEvent(
        execution_id=execution_id,
        event_type=ExecutionEventType(event_type),
        executor=executor,
        payload=payload,
        metadata=metadata or {},
    )
    await store.append(event)
    await _broadcast_event(event)
    return event


async def get_block_execution(
    execution_id: UUID, *, auth: AuthContext
) -> BlockExecution | None:
    """Retrieve a BlockExecution with its full event stream."""
    doc = await BlockExecutionDocument.find_one(
        {"execution_id": execution_id, "tenant_id": auth.tenant_id}
    )
    if doc is None:
        return None

    store = MongoEventStore(tenant_id=auth.tenant_id)
    events = await store.get_events(execution_id)

    return BlockExecution(
        id=doc.execution_id,
        node_reference_id=doc.node_reference_id,
        work_block_id=doc.work_block_id,
        work_block_version=doc.work_block_version,
        events=events,
    )


async def start_flow_execution(
    *,
    flow_id: UUID,
    flow_version: int,
    contract_execution_id: UUID | None = None,
    auth: AuthContext,
) -> FlowExecution:
    """Create a new FlowExecution and emit a CREATED event."""
    execution_id = uuid4()
    store = MongoEventStore(tenant_id=auth.tenant_id)

    created_event = ExecutionEvent(
        execution_id=execution_id,
        event_type=ExecutionEventType.CREATED,
    )
    await store.append(created_event)
    await _broadcast_event(created_event)

    doc = FlowExecutionDocument(
        execution_id=execution_id,
        flow_id=flow_id,
        flow_version=flow_version,
        contract_execution_id=contract_execution_id,
        tenant_id=auth.tenant_id,
    )
    await doc.insert()

    return FlowExecution(
        id=execution_id,
        flow_id=flow_id,
        flow_version=flow_version,
        events=[created_event],
    )


async def get_flow_execution(
    execution_id: UUID, *, auth: AuthContext
) -> FlowExecution | None:
    """Retrieve a FlowExecution with its events."""
    doc = await FlowExecutionDocument.find_one(
        {"execution_id": execution_id, "tenant_id": auth.tenant_id}
    )
    if doc is None:
        return None

    store = MongoEventStore(tenant_id=auth.tenant_id)
    events = await store.get_events(execution_id)

    return FlowExecution(
        id=doc.execution_id,
        flow_id=doc.flow_id,
        flow_version=doc.flow_version,
        block_executions=doc.block_execution_ids,
        events=events,
    )


async def start_contract_execution(
    *,
    contract_id: UUID,
    contract_version: int,
    auth: AuthContext,
) -> ContractExecution:
    """Create a new ContractExecution and emit a CREATED event."""
    execution_id = uuid4()
    store = MongoEventStore(tenant_id=auth.tenant_id)

    created_event = ExecutionEvent(
        execution_id=execution_id,
        event_type=ExecutionEventType.CREATED,
    )
    await store.append(created_event)
    await _broadcast_event(created_event)

    doc = ContractExecutionDocument(
        execution_id=execution_id,
        contract_id=contract_id,
        contract_version=contract_version,
        tenant_id=auth.tenant_id,
    )
    await doc.insert()

    return ContractExecution(
        id=execution_id,
        contract_id=contract_id,
        contract_version=contract_version,
        events=[created_event],
    )


async def get_execution_events(
    execution_id: UUID,
    *,
    after: datetime | None = None,
    auth: AuthContext,
) -> list[ExecutionEvent]:
    """Retrieve execution events, optionally after a timestamp."""
    store = MongoEventStore(tenant_id=auth.tenant_id)
    return await store.get_events(execution_id, after=after)


async def list_block_executions(
    *,
    auth: AuthContext,
    flow_execution_id: UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """List block executions as summary dicts (without full event replay)."""
    query: dict = {"tenant_id": auth.tenant_id}
    if flow_execution_id:
        query["flow_execution_id"] = flow_execution_id
    docs = await BlockExecutionDocument.find(
        query, skip=offset, limit=limit
    ).to_list()
    return [
        {
            "execution_id": doc.execution_id,
            "node_reference_id": doc.node_reference_id,
            "work_block_id": doc.work_block_id,
            "work_block_version": doc.work_block_version,
            "flow_execution_id": doc.flow_execution_id,
            "created_at": doc.created_at,
        }
        for doc in docs
    ]
