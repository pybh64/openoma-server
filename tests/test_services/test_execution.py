"""Tests for execution service — event sourcing, state derivation, lifecycle."""

from uuid import uuid4

import pytest
from openoma.execution.types import ExecutionOutcome, ExecutorInfo

from openoma_server.auth.context import CurrentUser
from openoma_server.services.execution import (
    add_block_to_flow_execution,
    add_flow_to_contract_execution,
    assign_executor_to_block,
    cancel_block_execution,
    complete_block_execution,
    create_block_execution,
    create_contract_execution,
    create_flow_execution,
    fail_block_execution,
    get_block_execution,
    get_contract_execution,
    get_events,
    get_flow_execution,
    list_block_executions,
    list_contract_executions,
    list_flow_executions,
    produce_block_outcome,
    refresh_contract_state,
    refresh_flow_state,
    start_block_execution,
)

pytestmark = pytest.mark.asyncio

USER = CurrentUser(id="test-user", email="test@example.com")
WB_ID = uuid4()
FLOW_ID = uuid4()
CONTRACT_ID = uuid4()


# ── BlockExecution Tests ───────────────────────────────────────────


async def test_create_block_execution():
    node_id = uuid4()
    doc = await create_block_execution(
        work_block_id=WB_ID,
        work_block_version=1,
        node_reference_id=node_id,
        user=USER,
    )
    assert doc.execution_id is not None
    assert doc.work_block_id == WB_ID
    assert doc.state == "pending"

    # Should have a CREATED event
    events = await get_events(doc.execution_id)
    assert len(events) == 1
    assert events[0].event_type == "created"


async def test_block_execution_full_lifecycle():
    """Test the full happy path: create → assign → start → outcome → complete."""
    doc = await create_block_execution(
        work_block_id=WB_ID, work_block_version=1, node_reference_id=uuid4()
    )
    eid = doc.execution_id

    # Assign executor
    doc = await assign_executor_to_block(
        eid, ExecutorInfo(type="human", identifier="alice@test.com")
    )
    assert doc.state == "pending"  # Assignment alone doesn't change state

    # Start
    doc = await start_block_execution(eid)
    assert doc.state == "in_progress"

    # Produce outcome
    doc = await produce_block_outcome(eid, ExecutionOutcome(value={"approved": True}))
    assert doc.state == "in_progress"
    assert doc.outcome is not None
    assert doc.outcome.value == {"approved": True}

    # Complete
    doc = await complete_block_execution(eid)
    assert doc.state == "completed"
    assert doc.outcome is not None
    assert doc.outcome.value == {"approved": True}

    # Verify event stream
    events = await get_events(eid)
    event_types = [e.event_type for e in events]
    assert event_types == [
        "created",
        "executor_assigned",
        "started",
        "outcome_produced",
        "completed",
    ]


async def test_block_execution_fail():
    doc = await create_block_execution(
        work_block_id=WB_ID, work_block_version=1, node_reference_id=uuid4()
    )
    doc = await start_block_execution(doc.execution_id)
    assert doc.state == "in_progress"

    doc = await fail_block_execution(doc.execution_id, metadata={"reason": "timeout"})
    assert doc.state == "failed"


async def test_block_execution_cancel():
    doc = await create_block_execution(
        work_block_id=WB_ID, work_block_version=1, node_reference_id=uuid4()
    )
    doc = await cancel_block_execution(doc.execution_id)
    assert doc.state == "cancelled"


async def test_get_block_execution():
    doc = await create_block_execution(
        work_block_id=WB_ID, work_block_version=1, node_reference_id=uuid4()
    )
    fetched = await get_block_execution(doc.execution_id)
    assert fetched is not None
    assert fetched.execution_id == doc.execution_id


async def test_get_block_execution_not_found():
    result = await get_block_execution(uuid4())
    assert result is None


async def test_list_block_executions():
    wb_id = uuid4()
    await create_block_execution(
        work_block_id=wb_id, work_block_version=1, node_reference_id=uuid4()
    )
    await create_block_execution(
        work_block_id=wb_id, work_block_version=1, node_reference_id=uuid4()
    )

    results = await list_block_executions(work_block_id=wb_id)
    assert len(results) >= 2


async def test_list_block_executions_by_state():
    wb_id = uuid4()
    doc1 = await create_block_execution(
        work_block_id=wb_id, work_block_version=1, node_reference_id=uuid4()
    )
    await create_block_execution(
        work_block_id=wb_id, work_block_version=1, node_reference_id=uuid4()
    )
    await start_block_execution(doc1.execution_id)

    in_progress = await list_block_executions(work_block_id=wb_id, state="in_progress")
    assert len(in_progress) >= 1

    pending = await list_block_executions(work_block_id=wb_id, state="pending")
    assert len(pending) >= 1


# ── FlowExecution Tests ───────────────────────────────────────────


async def test_create_flow_execution():
    doc = await create_flow_execution(flow_id=FLOW_ID, flow_version=1, user=USER)
    assert doc.execution_id is not None
    assert doc.flow_id == FLOW_ID
    assert doc.state == "pending"


async def test_add_block_to_flow_execution():
    flow_doc = await create_flow_execution(flow_id=FLOW_ID, flow_version=1)
    block_doc = await create_block_execution(
        work_block_id=WB_ID,
        work_block_version=1,
        node_reference_id=uuid4(),
        flow_execution_id=flow_doc.execution_id,
    )

    flow_doc = await add_block_to_flow_execution(flow_doc.execution_id, block_doc.execution_id)
    assert block_doc.execution_id in flow_doc.block_executions


async def test_add_block_idempotent():
    flow_doc = await create_flow_execution(flow_id=FLOW_ID, flow_version=1)
    block_id = uuid4()
    block_doc = await create_block_execution(
        work_block_id=WB_ID,
        work_block_version=1,
        node_reference_id=block_id,
        flow_execution_id=flow_doc.execution_id,
    )

    await add_block_to_flow_execution(flow_doc.execution_id, block_doc.execution_id)
    flow_doc = await add_block_to_flow_execution(flow_doc.execution_id, block_doc.execution_id)
    assert flow_doc.block_executions.count(block_doc.execution_id) == 1


async def test_refresh_flow_state_all_completed():
    flow_doc = await create_flow_execution(flow_id=FLOW_ID, flow_version=1)
    node1 = uuid4()
    node2 = uuid4()

    b1 = await create_block_execution(
        work_block_id=WB_ID,
        work_block_version=1,
        node_reference_id=node1,
        flow_execution_id=flow_doc.execution_id,
    )
    b2 = await create_block_execution(
        work_block_id=WB_ID,
        work_block_version=1,
        node_reference_id=node2,
        flow_execution_id=flow_doc.execution_id,
    )

    await add_block_to_flow_execution(flow_doc.execution_id, b1.execution_id)
    await add_block_to_flow_execution(flow_doc.execution_id, b2.execution_id)

    # Complete both blocks
    await start_block_execution(b1.execution_id)
    await complete_block_execution(b1.execution_id)
    await start_block_execution(b2.execution_id)
    await complete_block_execution(b2.execution_id)

    # terminal_node_ids = both nodes (both are terminal in this simple flow)
    flow_doc = await refresh_flow_state(flow_doc.execution_id, terminal_node_ids={node1, node2})
    assert flow_doc.state == "completed"


async def test_refresh_flow_state_one_failed():
    flow_doc = await create_flow_execution(flow_id=FLOW_ID, flow_version=1)
    node1 = uuid4()

    b1 = await create_block_execution(
        work_block_id=WB_ID,
        work_block_version=1,
        node_reference_id=node1,
        flow_execution_id=flow_doc.execution_id,
    )
    await add_block_to_flow_execution(flow_doc.execution_id, b1.execution_id)

    await start_block_execution(b1.execution_id)
    await fail_block_execution(b1.execution_id)

    flow_doc = await refresh_flow_state(flow_doc.execution_id, terminal_node_ids={node1})
    assert flow_doc.state == "failed"


async def test_get_flow_execution():
    doc = await create_flow_execution(flow_id=FLOW_ID, flow_version=1)
    fetched = await get_flow_execution(doc.execution_id)
    assert fetched is not None
    assert fetched.flow_id == FLOW_ID


async def test_list_flow_executions():
    fid = uuid4()
    await create_flow_execution(flow_id=fid, flow_version=1)
    await create_flow_execution(flow_id=fid, flow_version=1)

    results = await list_flow_executions(flow_id=fid)
    assert len(results) >= 2


# ── ContractExecution Tests ────────────────────────────────────────


async def test_create_contract_execution():
    doc = await create_contract_execution(contract_id=CONTRACT_ID, contract_version=1, user=USER)
    assert doc.execution_id is not None
    assert doc.contract_id == CONTRACT_ID
    assert doc.state == "pending"


async def test_add_flow_to_contract_execution():
    ce = await create_contract_execution(contract_id=CONTRACT_ID, contract_version=1)
    fe = await create_flow_execution(
        flow_id=FLOW_ID,
        flow_version=1,
        contract_execution_id=ce.execution_id,
    )

    ce = await add_flow_to_contract_execution(ce.execution_id, fe.execution_id)
    assert fe.execution_id in ce.flow_executions


async def test_refresh_contract_state_all_completed():
    ce = await create_contract_execution(contract_id=CONTRACT_ID, contract_version=1)
    fe1 = await create_flow_execution(
        flow_id=uuid4(),
        flow_version=1,
        contract_execution_id=ce.execution_id,
    )
    fe2 = await create_flow_execution(
        flow_id=uuid4(),
        flow_version=1,
        contract_execution_id=ce.execution_id,
    )

    await add_flow_to_contract_execution(ce.execution_id, fe1.execution_id)
    await add_flow_to_contract_execution(ce.execution_id, fe2.execution_id)

    # Mark both flows as completed directly on the doc
    from openoma_server.models.execution import FlowExecutionDoc

    for fe_id in [fe1.execution_id, fe2.execution_id]:
        fe_doc = await FlowExecutionDoc.find_one(FlowExecutionDoc.execution_id == fe_id)
        fe_doc.state = "completed"
        await fe_doc.save()

    ce = await refresh_contract_state(ce.execution_id)
    assert ce.state == "completed"


async def test_refresh_contract_state_one_failed():
    ce = await create_contract_execution(contract_id=CONTRACT_ID, contract_version=1)
    fe = await create_flow_execution(
        flow_id=uuid4(),
        flow_version=1,
        contract_execution_id=ce.execution_id,
    )
    await add_flow_to_contract_execution(ce.execution_id, fe.execution_id)

    from openoma_server.models.execution import FlowExecutionDoc

    fe_doc = await FlowExecutionDoc.find_one(FlowExecutionDoc.execution_id == fe.execution_id)
    fe_doc.state = "failed"
    await fe_doc.save()

    ce = await refresh_contract_state(ce.execution_id)
    assert ce.state == "failed"


async def test_get_contract_execution():
    doc = await create_contract_execution(contract_id=CONTRACT_ID, contract_version=1)
    fetched = await get_contract_execution(doc.execution_id)
    assert fetched is not None


async def test_list_contract_executions():
    cid = uuid4()
    await create_contract_execution(contract_id=cid, contract_version=1)
    await create_contract_execution(contract_id=cid, contract_version=1)

    results = await list_contract_executions(contract_id=cid)
    assert len(results) >= 2


# ── Event Stream Tests ─────────────────────────────────────────────


async def test_event_stream_immutable():
    """Events are append-only — full history is preserved."""
    doc = await create_block_execution(
        work_block_id=WB_ID, work_block_version=1, node_reference_id=uuid4()
    )
    eid = doc.execution_id

    await start_block_execution(eid)
    await complete_block_execution(eid)

    events = await get_events(eid)
    assert len(events) == 3
    assert events[0].event_type == "created"
    assert events[1].event_type == "started"
    assert events[2].event_type == "completed"

    # All events reference the same execution
    assert all(e.execution_id == eid for e in events)

    # Events are in chronological order
    for i in range(len(events) - 1):
        assert events[i].timestamp <= events[i + 1].timestamp


async def test_block_execution_roundtrip():
    """Verify doc → core → back preserves data."""
    doc = await create_block_execution(
        work_block_id=WB_ID, work_block_version=1, node_reference_id=uuid4()
    )
    core = doc.to_core()
    assert core.id == doc.execution_id
    assert core.work_block_id == WB_ID
    assert core.state.value == "pending"
