"""Tests for MongoExecutionStore."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from openoma.execution.block_execution import BlockExecution
from openoma.execution.contract_execution import ContractExecution
from openoma.execution.flow_execution import FlowExecution
from openoma.execution.types import ExecutionState

from openoma_server.store.execution_store import MongoExecutionStore


@pytest.fixture
def store():
    return MongoExecutionStore()


def _make_block_execution(*, state=ExecutionState.PENDING, flow_exec_id=None, wb_id=None):
    return BlockExecution(
        id=uuid4(),
        flow_execution_id=flow_exec_id,
        node_reference_id=uuid4(),
        work_block_id=wb_id or uuid4(),
        work_block_version=1,
        state=state,
        created_at=datetime.now(UTC),
    )


def _make_flow_execution(*, state=ExecutionState.PENDING, contract_exec_id=None, flow_id=None):
    return FlowExecution(
        id=uuid4(),
        contract_execution_id=contract_exec_id,
        flow_id=flow_id or uuid4(),
        flow_version=1,
        block_executions=[],
        state=state,
        created_at=datetime.now(UTC),
    )


def _make_contract_execution(*, state=ExecutionState.PENDING, contract_id=None):
    return ContractExecution(
        id=uuid4(),
        contract_id=contract_id or uuid4(),
        contract_version=1,
        flow_executions=[],
        sub_contract_executions=[],
        assessment_executions=[],
        state=state,
        created_at=datetime.now(UTC),
    )


# ── BlockExecution tests ───────────────────────────────────────────────


class TestBlockExecutionStore:
    @pytest.mark.asyncio
    async def test_save_and_get(self, store):
        be = _make_block_execution()
        await store.save_block_execution(be)
        result = await store.get_block_execution(be.id)
        assert result is not None
        assert result.id == be.id
        assert result.state == ExecutionState.PENDING

    @pytest.mark.asyncio
    async def test_upsert_updates_state(self, store):
        be = _make_block_execution()
        await store.save_block_execution(be)

        updated = BlockExecution(
            id=be.id,
            flow_execution_id=be.flow_execution_id,
            node_reference_id=be.node_reference_id,
            work_block_id=be.work_block_id,
            work_block_version=be.work_block_version,
            state=ExecutionState.IN_PROGRESS,
            created_at=be.created_at,
        )
        await store.save_block_execution(updated)

        result = await store.get_block_execution(be.id)
        assert result.state == ExecutionState.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, store):
        result = await store.get_block_execution(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_batch_get(self, store):
        be1 = _make_block_execution()
        be2 = _make_block_execution()
        await store.save_block_execution(be1)
        await store.save_block_execution(be2)
        results = await store.get_block_executions([be1.id, be2.id, uuid4()])
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_list_by_flow_execution(self, store):
        feid = uuid4()
        be1 = _make_block_execution(flow_exec_id=feid)
        be2 = _make_block_execution(flow_exec_id=feid)
        be3 = _make_block_execution()  # different flow
        await store.save_block_execution(be1)
        await store.save_block_execution(be2)
        await store.save_block_execution(be3)

        results = await store.list_block_executions(flow_execution_id=feid)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_list_by_state(self, store):
        await store.save_block_execution(_make_block_execution(state=ExecutionState.PENDING))
        await store.save_block_execution(
            _make_block_execution(state=ExecutionState.IN_PROGRESS)
        )
        results = await store.list_block_executions(state=ExecutionState.PENDING)
        assert all(r.state == ExecutionState.PENDING for r in results)


# ── FlowExecution tests ───────────────────────────────────────────────


class TestFlowExecutionStore:
    @pytest.mark.asyncio
    async def test_save_and_get(self, store):
        fe = _make_flow_execution()
        await store.save_flow_execution(fe)
        result = await store.get_flow_execution(fe.id)
        assert result is not None
        assert result.id == fe.id

    @pytest.mark.asyncio
    async def test_upsert_updates_state(self, store):
        fe = _make_flow_execution()
        await store.save_flow_execution(fe)

        updated = FlowExecution(
            id=fe.id,
            contract_execution_id=fe.contract_execution_id,
            flow_id=fe.flow_id,
            flow_version=fe.flow_version,
            block_executions=[uuid4()],
            state=ExecutionState.COMPLETED,
            created_at=fe.created_at,
        )
        await store.save_flow_execution(updated)

        result = await store.get_flow_execution(fe.id)
        assert result.state == ExecutionState.COMPLETED
        assert len(result.block_executions) == 1

    @pytest.mark.asyncio
    async def test_list_by_contract_execution(self, store):
        ceid = uuid4()
        fe1 = _make_flow_execution(contract_exec_id=ceid)
        fe2 = _make_flow_execution(contract_exec_id=ceid)
        fe3 = _make_flow_execution()
        await store.save_flow_execution(fe1)
        await store.save_flow_execution(fe2)
        await store.save_flow_execution(fe3)

        results = await store.list_flow_executions(contract_execution_id=ceid)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_batch_get(self, store):
        fe1 = _make_flow_execution()
        fe2 = _make_flow_execution()
        await store.save_flow_execution(fe1)
        await store.save_flow_execution(fe2)
        results = await store.get_flow_executions([fe1.id, fe2.id])
        assert len(results) == 2


# ── ContractExecution tests ────────────────────────────────────────────


class TestContractExecutionStore:
    @pytest.mark.asyncio
    async def test_save_and_get(self, store):
        ce = _make_contract_execution()
        await store.save_contract_execution(ce)
        result = await store.get_contract_execution(ce.id)
        assert result is not None
        assert result.id == ce.id

    @pytest.mark.asyncio
    async def test_upsert_updates_state(self, store):
        ce = _make_contract_execution()
        await store.save_contract_execution(ce)

        updated = ContractExecution(
            id=ce.id,
            contract_id=ce.contract_id,
            contract_version=ce.contract_version,
            flow_executions=[uuid4()],
            sub_contract_executions=[],
            assessment_executions=[],
            state=ExecutionState.IN_PROGRESS,
            created_at=ce.created_at,
        )
        await store.save_contract_execution(updated)

        result = await store.get_contract_execution(ce.id)
        assert result.state == ExecutionState.IN_PROGRESS
        assert len(result.flow_executions) == 1

    @pytest.mark.asyncio
    async def test_list_by_contract_id(self, store):
        cid = uuid4()
        ce1 = _make_contract_execution(contract_id=cid)
        ce2 = _make_contract_execution(contract_id=cid)
        ce3 = _make_contract_execution()
        await store.save_contract_execution(ce1)
        await store.save_contract_execution(ce2)
        await store.save_contract_execution(ce3)

        results = await store.list_contract_executions(contract_id=cid)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_list_by_state(self, store):
        await store.save_contract_execution(
            _make_contract_execution(state=ExecutionState.PENDING)
        )
        await store.save_contract_execution(
            _make_contract_execution(state=ExecutionState.COMPLETED)
        )
        results = await store.list_contract_executions(state=ExecutionState.PENDING)
        assert all(r.state == ExecutionState.PENDING for r in results)

    @pytest.mark.asyncio
    async def test_batch_get(self, store):
        ce1 = _make_contract_execution()
        ce2 = _make_contract_execution()
        await store.save_contract_execution(ce1)
        await store.save_contract_execution(ce2)
        results = await store.get_contract_executions([ce1.id, ce2.id])
        assert len(results) == 2
