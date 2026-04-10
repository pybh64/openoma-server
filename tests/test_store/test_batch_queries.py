"""Tests for batch / bulk query methods in store layer."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from openoma.core.contract import Contract, RequiredOutcome
from openoma.core.flow import Flow, NodeReference
from openoma.core.work_block import WorkBlock
from openoma.execution.events import ExecutionEvent, ExecutionEventType

from openoma_server.store.definition_store import MongoDefinitionStore
from openoma_server.store.event_store import MongoEventStore


@pytest.fixture
def def_store():
    return MongoDefinitionStore()


@pytest.fixture
def evt_store():
    return MongoEventStore()


# ── Helpers ────────────────────────────────────────────────────────────


def _make_work_block(*, name: str = "block", version: int = 1, entity_id=None):
    return WorkBlock(
        id=entity_id or uuid4(),
        version=version,
        name=name,
        description=f"{name} description",
        created_at=datetime.now(UTC),
    )


def _make_flow(*, name: str = "flow", version: int = 1, entity_id=None):
    return Flow(
        id=entity_id or uuid4(),
        version=version,
        name=name,
        description=f"{name} description",
        created_at=datetime.now(UTC),
        nodes=[
            NodeReference(id=uuid4(), target_id=uuid4(), target_version=1),
        ],
        edges=[],
    )


def _make_contract(*, name: str = "contract", version: int = 1, entity_id=None):
    return Contract(
        id=entity_id or uuid4(),
        version=version,
        name=name,
        description=f"{name} description",
        created_at=datetime.now(UTC),
        owners=[],
        work_flows=[],
        sub_contracts=[],
        required_outcomes=[],
    )


def _make_required_outcome(*, name: str = "outcome", version: int = 1, entity_id=None):
    return RequiredOutcome(
        id=entity_id or uuid4(),
        version=version,
        name=name,
        description=f"{name} description",
        created_at=datetime.now(UTC),
        assessment_bindings=[],
    )


def _make_event(execution_id=None, event_type=ExecutionEventType.CREATED, ts_offset_seconds=0):
    return ExecutionEvent(
        id=uuid4(),
        timestamp=datetime.now(UTC) + timedelta(seconds=ts_offset_seconds),
        execution_id=execution_id or uuid4(),
        event_type=event_type,
    )


# ── WorkBlock batch tests ──────────────────────────────────────────────


class TestBatchGetWorkBlocks:
    @pytest.mark.asyncio
    async def test_batch_get_work_blocks(self, def_store):
        blocks = [_make_work_block(name=f"wb-{i}") for i in range(3)]
        for b in blocks:
            await def_store.save_work_block(b)

        refs = [(b.id, b.version) for b in blocks]
        results = await def_store.get_work_blocks(refs)
        assert len(results) == 3
        result_ids = {r.id for r in results}
        assert result_ids == {b.id for b in blocks}

    @pytest.mark.asyncio
    async def test_batch_get_work_blocks_empty(self, def_store):
        results = await def_store.get_work_blocks([])
        assert results == []

    @pytest.mark.asyncio
    async def test_batch_get_work_blocks_partial(self, def_store):
        wb = _make_work_block()
        await def_store.save_work_block(wb)

        refs = [(wb.id, wb.version), (uuid4(), 99)]
        results = await def_store.get_work_blocks(refs)
        assert len(results) == 1
        assert results[0].id == wb.id


# ── Flow batch tests ──────────────────────────────────────────────────


class TestBatchGetFlows:
    @pytest.mark.asyncio
    async def test_batch_get_flows(self, def_store):
        flows = [_make_flow(name=f"flow-{i}") for i in range(3)]
        for f in flows:
            await def_store.save_flow(f)

        refs = [(f.id, f.version) for f in flows]
        results = await def_store.get_flows(refs)
        assert len(results) == 3
        result_ids = {r.id for r in results}
        assert result_ids == {f.id for f in flows}


# ── Contract batch tests ──────────────────────────────────────────────


class TestBatchGetContracts:
    @pytest.mark.asyncio
    async def test_batch_get_contracts(self, def_store):
        contracts = [_make_contract(name=f"c-{i}") for i in range(3)]
        for c in contracts:
            await def_store.save_contract(c)

        refs = [(c.id, c.version) for c in contracts]
        results = await def_store.get_contracts(refs)
        assert len(results) == 3
        result_ids = {r.id for r in results}
        assert result_ids == {c.id for c in contracts}


# ── RequiredOutcome batch tests ───────────────────────────────────────


class TestBatchGetRequiredOutcomes:
    @pytest.mark.asyncio
    async def test_batch_get_required_outcomes(self, def_store):
        outcomes = [_make_required_outcome(name=f"ro-{i}") for i in range(3)]
        for o in outcomes:
            await def_store.save_required_outcome(o)

        refs = [(o.id, o.version) for o in outcomes]
        results = await def_store.get_required_outcomes(refs)
        assert len(results) == 3
        result_ids = {r.id for r in results}
        assert result_ids == {o.id for o in outcomes}


# ── Event batch tests ────────────────────────────────────────────────


class TestBatchGetLatestEvents:
    @pytest.mark.asyncio
    async def test_batch_get_latest_events(self, evt_store):
        eid1, eid2 = uuid4(), uuid4()
        # eid1: two events, latest is STARTED
        await evt_store.append(
            _make_event(execution_id=eid1, event_type=ExecutionEventType.CREATED)
        )
        await evt_store.append(
            _make_event(
                execution_id=eid1,
                event_type=ExecutionEventType.STARTED,
                ts_offset_seconds=5,
            )
        )
        # eid2: one event
        await evt_store.append(
            _make_event(execution_id=eid2, event_type=ExecutionEventType.CREATED)
        )

        results = await evt_store.get_latest_events([eid1, eid2])
        assert len(results) == 2
        by_eid = {e.execution_id: e for e in results}
        assert by_eid[eid1].event_type == ExecutionEventType.STARTED
        assert by_eid[eid2].event_type == ExecutionEventType.CREATED

    @pytest.mark.asyncio
    async def test_batch_get_latest_events_empty(self, evt_store):
        results = await evt_store.get_latest_events([])
        assert results == []
