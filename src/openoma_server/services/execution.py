"""Execution service — event-sourced execution lifecycle management.

Provides functions to create executions, append events, and derive state.
Follows the openoma event sourcing + CQRS pattern:
- EventStore (ExecutionEventDoc) is the authoritative log
- Execution docs (Block/Flow/Contract) are read-side projections
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from openoma.execution.block_execution import BlockExecution, derive_block_state
from openoma.execution.contract_execution import (
    ContractExecution,
    derive_contract_state,
)
from openoma.execution.events import ExecutionEvent, ExecutionEventType
from openoma.execution.flow_execution import FlowExecution, derive_flow_state
from openoma.execution.types import (
    ExecutionOutcome,
    ExecutionState,
    ExecutorInfo,
)

from openoma_server.auth.context import CurrentUser
from openoma_server.models.execution import (
    BlockExecutionDoc,
    ContractExecutionDoc,
    ExecutionEventDoc,
    FlowExecutionDoc,
)

# ── Event helpers ──────────────────────────────────────────────────


async def _append_event(
    execution_id: UUID,
    event_type: ExecutionEventType,
    executor: ExecutorInfo | None = None,
    outcome: ExecutionOutcome | None = None,
    metadata: dict | None = None,
) -> ExecutionEventDoc:
    event = ExecutionEvent(
        id=uuid4(),
        timestamp=datetime.now(UTC),
        execution_id=execution_id,
        event_type=event_type,
        executor=executor,
        outcome=outcome,
        metadata=metadata or {},
    )
    doc = ExecutionEventDoc.from_core(event)
    await doc.insert()
    return doc


async def get_events(execution_id: UUID) -> list[ExecutionEventDoc]:
    return (
        await ExecutionEventDoc.find(
            ExecutionEventDoc.execution_id == execution_id,
        )
        .sort("+timestamp")
        .to_list()
    )


async def get_latest_event(execution_id: UUID) -> ExecutionEventDoc | None:
    return await ExecutionEventDoc.find_one(
        ExecutionEventDoc.execution_id == execution_id,
        sort=[("timestamp", -1)],
    )


# ── BlockExecution ─────────────────────────────────────────────────


async def create_block_execution(
    work_block_id: UUID,
    work_block_version: int,
    node_reference_id: UUID,
    flow_execution_id: UUID | None = None,
    user: CurrentUser | None = None,
) -> BlockExecutionDoc:
    execution_id = uuid4()

    be = BlockExecution(
        id=execution_id,
        flow_execution_id=flow_execution_id,
        node_reference_id=node_reference_id,
        work_block_id=work_block_id,
        work_block_version=work_block_version,
        state=ExecutionState.PENDING,
        created_at=datetime.now(UTC),
    )
    doc = BlockExecutionDoc.from_core(be)
    await doc.insert()

    await _append_event(execution_id, ExecutionEventType.CREATED)
    return doc


async def _refresh_block_state(execution_id: UUID) -> BlockExecutionDoc:
    """Re-derive state from events and persist the updated projection."""
    event_docs = await get_events(execution_id)
    events = [e.to_core() for e in event_docs]
    state = derive_block_state(events)

    doc = await BlockExecutionDoc.find_one(BlockExecutionDoc.execution_id == execution_id)
    if doc is None:
        raise ValueError(f"BlockExecution {execution_id} not found")

    doc.state = state.value
    await doc.save()
    return doc


async def assign_executor_to_block(execution_id: UUID, executor: ExecutorInfo) -> BlockExecutionDoc:
    await _append_event(execution_id, ExecutionEventType.EXECUTOR_ASSIGNED, executor=executor)
    return await _refresh_block_state(execution_id)


async def start_block_execution(execution_id: UUID) -> BlockExecutionDoc:
    await _append_event(execution_id, ExecutionEventType.STARTED)
    return await _refresh_block_state(execution_id)


async def produce_block_outcome(execution_id: UUID, outcome: ExecutionOutcome) -> BlockExecutionDoc:
    await _append_event(execution_id, ExecutionEventType.OUTCOME_PRODUCED, outcome=outcome)
    return await _refresh_block_state(execution_id)


async def complete_block_execution(execution_id: UUID) -> BlockExecutionDoc:
    await _append_event(execution_id, ExecutionEventType.COMPLETED)
    return await _refresh_block_state(execution_id)


async def fail_block_execution(
    execution_id: UUID, metadata: dict | None = None
) -> BlockExecutionDoc:
    await _append_event(execution_id, ExecutionEventType.FAILED, metadata=metadata)
    return await _refresh_block_state(execution_id)


async def cancel_block_execution(execution_id: UUID) -> BlockExecutionDoc:
    await _append_event(execution_id, ExecutionEventType.CANCELLED)
    return await _refresh_block_state(execution_id)


async def get_block_execution(execution_id: UUID) -> BlockExecutionDoc | None:
    return await BlockExecutionDoc.find_one(BlockExecutionDoc.execution_id == execution_id)


async def list_block_executions(
    work_block_id: UUID | None = None,
    flow_execution_id: UUID | None = None,
    state: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[BlockExecutionDoc]:
    filters = []
    if work_block_id:
        filters.append(BlockExecutionDoc.work_block_id == work_block_id)
    if flow_execution_id:
        filters.append(BlockExecutionDoc.flow_execution_id == flow_execution_id)
    if state:
        filters.append(BlockExecutionDoc.state == state)

    return (
        await BlockExecutionDoc.find(*filters)
        .sort("-created_at")
        .skip(offset)
        .limit(limit)
        .to_list()
    )


# ── FlowExecution ─────────────────────────────────────────────────


async def create_flow_execution(
    flow_id: UUID,
    flow_version: int,
    contract_execution_id: UUID | None = None,
    user: CurrentUser | None = None,
) -> FlowExecutionDoc:
    execution_id = uuid4()

    fe = FlowExecution(
        id=execution_id,
        contract_execution_id=contract_execution_id,
        flow_id=flow_id,
        flow_version=flow_version,
        state=ExecutionState.PENDING,
        created_at=datetime.now(UTC),
    )
    doc = FlowExecutionDoc.from_core(fe)
    await doc.insert()

    await _append_event(execution_id, ExecutionEventType.CREATED)
    return doc


async def add_block_to_flow_execution(
    flow_execution_id: UUID, block_execution_id: UUID
) -> FlowExecutionDoc:
    doc = await FlowExecutionDoc.find_one(FlowExecutionDoc.execution_id == flow_execution_id)
    if doc is None:
        raise ValueError(f"FlowExecution {flow_execution_id} not found")
    if block_execution_id not in doc.block_executions:
        doc.block_executions.append(block_execution_id)
        await doc.save()
    return doc


async def refresh_flow_state(
    flow_execution_id: UUID, terminal_node_ids: set[UUID] | None = None
) -> FlowExecutionDoc:
    """Re-derive flow state from child block execution states."""
    doc = await FlowExecutionDoc.find_one(FlowExecutionDoc.execution_id == flow_execution_id)
    if doc is None:
        raise ValueError(f"FlowExecution {flow_execution_id} not found")

    block_docs = await BlockExecutionDoc.find(
        {"execution_id": {"$in": doc.block_executions}}
    ).to_list()
    block_cores = [bd.to_core() for bd in block_docs]

    state = derive_flow_state(block_cores, terminal_node_ids or set())
    doc.state = state.value
    await doc.save()
    return doc


async def get_flow_execution(execution_id: UUID) -> FlowExecutionDoc | None:
    return await FlowExecutionDoc.find_one(FlowExecutionDoc.execution_id == execution_id)


async def list_flow_executions(
    flow_id: UUID | None = None,
    contract_execution_id: UUID | None = None,
    state: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[FlowExecutionDoc]:
    filters = []
    if flow_id:
        filters.append(FlowExecutionDoc.flow_id == flow_id)
    if contract_execution_id:
        filters.append(FlowExecutionDoc.contract_execution_id == contract_execution_id)
    if state:
        filters.append(FlowExecutionDoc.state == state)

    return (
        await FlowExecutionDoc.find(*filters)
        .sort("-created_at")
        .skip(offset)
        .limit(limit)
        .to_list()
    )


# ── ContractExecution ──────────────────────────────────────────────


async def create_contract_execution(
    contract_id: UUID,
    contract_version: int,
    user: CurrentUser | None = None,
) -> ContractExecutionDoc:
    execution_id = uuid4()

    ce = ContractExecution(
        id=execution_id,
        contract_id=contract_id,
        contract_version=contract_version,
        state=ExecutionState.PENDING,
        created_at=datetime.now(UTC),
    )
    doc = ContractExecutionDoc.from_core(ce)
    await doc.insert()

    await _append_event(execution_id, ExecutionEventType.CREATED)
    return doc


async def add_flow_to_contract_execution(
    contract_execution_id: UUID, flow_execution_id: UUID
) -> ContractExecutionDoc:
    doc = await ContractExecutionDoc.find_one(
        ContractExecutionDoc.execution_id == contract_execution_id
    )
    if doc is None:
        raise ValueError(f"ContractExecution {contract_execution_id} not found")
    if flow_execution_id not in doc.flow_executions:
        doc.flow_executions.append(flow_execution_id)
        await doc.save()
    return doc


async def refresh_contract_state(contract_execution_id: UUID) -> ContractExecutionDoc:
    """Re-derive contract state from child flow/sub-contract states."""
    doc = await ContractExecutionDoc.find_one(
        ContractExecutionDoc.execution_id == contract_execution_id
    )
    if doc is None:
        raise ValueError(f"ContractExecution {contract_execution_id} not found")

    flow_docs = await FlowExecutionDoc.find(
        {"execution_id": {"$in": doc.flow_executions}}
    ).to_list()
    flow_states = [ExecutionState(fd.state) for fd in flow_docs]

    sub_docs = await ContractExecutionDoc.find(
        {"execution_id": {"$in": doc.sub_contract_executions}}
    ).to_list()
    sub_states = [ExecutionState(sd.state) for sd in sub_docs]

    state = derive_contract_state(flow_states, sub_states)
    doc.state = state.value
    await doc.save()
    return doc


async def get_contract_execution(execution_id: UUID) -> ContractExecutionDoc | None:
    return await ContractExecutionDoc.find_one(ContractExecutionDoc.execution_id == execution_id)


async def list_contract_executions(
    contract_id: UUID | None = None,
    state: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[ContractExecutionDoc]:
    filters = []
    if contract_id:
        filters.append(ContractExecutionDoc.contract_id == contract_id)
    if state:
        filters.append(ContractExecutionDoc.state == state)

    return (
        await ContractExecutionDoc.find(*filters)
        .sort("-created_at")
        .skip(offset)
        .limit(limit)
        .to_list()
    )
