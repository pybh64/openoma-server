"""Tests for MongoDefinitionStore."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from openoma.core.contract import Contract, RequiredOutcome
from openoma.core.flow import Flow, NodeReference
from openoma.core.work_block import WorkBlock

from openoma_server.store.definition_store import MongoDefinitionStore


@pytest.fixture
def store():
    return MongoDefinitionStore()


def _make_work_block(*, name: str = "test-block", version: int = 1, entity_id=None):
    return WorkBlock(
        id=entity_id or uuid4(),
        version=version,
        name=name,
        description=f"{name} description",
        created_at=datetime.now(UTC),
    )


def _make_flow(*, name: str = "test-flow", version: int = 1, entity_id=None):
    fid = entity_id or uuid4()
    node_id = uuid4()
    return Flow(
        id=fid,
        version=version,
        name=name,
        description=f"{name} description",
        created_at=datetime.now(UTC),
        nodes=[
            NodeReference(
                id=node_id,
                target_id=uuid4(),
                target_version=1,
            )
        ],
        edges=[],
    )


def _make_contract(*, name: str = "test-contract", version: int = 1, entity_id=None):
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


def _make_required_outcome(*, name: str = "test-outcome", version: int = 1, entity_id=None):
    return RequiredOutcome(
        id=entity_id or uuid4(),
        version=version,
        name=name,
        description=f"{name} description",
        created_at=datetime.now(UTC),
        assessment_bindings=[],
    )


# ── WorkBlock tests ────────────────────────────────────────────────────


class TestWorkBlockStore:
    @pytest.mark.asyncio
    async def test_save_and_get(self, store):
        wb = _make_work_block()
        await store.save_work_block(wb)
        result = await store.get_work_block(wb.id, wb.version)
        assert result is not None
        assert result.id == wb.id
        assert result.name == wb.name

    @pytest.mark.asyncio
    async def test_duplicate_raises(self, store):
        wb = _make_work_block()
        await store.save_work_block(wb)
        with pytest.raises(ValueError, match="already exists"):
            await store.save_work_block(wb)

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, store):
        result = await store.get_work_block(uuid4(), 1)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_latest(self, store):
        eid = uuid4()
        await store.save_work_block(_make_work_block(entity_id=eid, version=1))
        await store.save_work_block(_make_work_block(entity_id=eid, version=2, name="updated"))
        result = await store.get_latest_work_block(eid)
        assert result is not None
        assert result.version == 2
        assert result.name == "updated"

    @pytest.mark.asyncio
    async def test_batch_get(self, store):
        wb1 = _make_work_block(name="batch-1")
        wb2 = _make_work_block(name="batch-2")
        await store.save_work_block(wb1)
        await store.save_work_block(wb2)
        results = await store.get_work_blocks([(wb1.id, 1), (wb2.id, 1), (uuid4(), 99)])
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_list(self, store):
        eid = uuid4()
        await store.save_work_block(_make_work_block(entity_id=eid, version=1))
        await store.save_work_block(_make_work_block(entity_id=eid, version=2))
        results = await store.list_work_blocks()
        # list_latest returns only latest per entity_id
        assert len(results) >= 1


# ── Flow tests ─────────────────────────────────────────────────────────


class TestFlowStore:
    @pytest.mark.asyncio
    async def test_save_and_get(self, store):
        flow = _make_flow()
        await store.save_flow(flow)
        result = await store.get_flow(flow.id, flow.version)
        assert result is not None
        assert result.id == flow.id

    @pytest.mark.asyncio
    async def test_duplicate_raises(self, store):
        flow = _make_flow()
        await store.save_flow(flow)
        with pytest.raises(ValueError, match="already exists"):
            await store.save_flow(flow)

    @pytest.mark.asyncio
    async def test_get_latest(self, store):
        eid = uuid4()
        await store.save_flow(_make_flow(entity_id=eid, version=1))
        await store.save_flow(_make_flow(entity_id=eid, version=2, name="v2"))
        result = await store.get_latest_flow(eid)
        assert result is not None
        assert result.version == 2

    @pytest.mark.asyncio
    async def test_batch_get(self, store):
        f1 = _make_flow(name="f1")
        f2 = _make_flow(name="f2")
        await store.save_flow(f1)
        await store.save_flow(f2)
        results = await store.get_flows([(f1.id, 1), (f2.id, 1)])
        assert len(results) == 2


# ── Contract tests ─────────────────────────────────────────────────────


class TestContractStore:
    @pytest.mark.asyncio
    async def test_save_and_get(self, store):
        c = _make_contract()
        await store.save_contract(c)
        result = await store.get_contract(c.id, c.version)
        assert result is not None
        assert result.id == c.id

    @pytest.mark.asyncio
    async def test_duplicate_raises(self, store):
        c = _make_contract()
        await store.save_contract(c)
        with pytest.raises(ValueError, match="already exists"):
            await store.save_contract(c)

    @pytest.mark.asyncio
    async def test_get_latest(self, store):
        eid = uuid4()
        await store.save_contract(_make_contract(entity_id=eid, version=1))
        await store.save_contract(_make_contract(entity_id=eid, version=2, name="v2"))
        result = await store.get_latest_contract(eid)
        assert result is not None
        assert result.version == 2

    @pytest.mark.asyncio
    async def test_batch_get(self, store):
        c1 = _make_contract(name="c1")
        c2 = _make_contract(name="c2")
        await store.save_contract(c1)
        await store.save_contract(c2)
        results = await store.get_contracts([(c1.id, 1), (c2.id, 1)])
        assert len(results) == 2


# ── RequiredOutcome tests ──────────────────────────────────────────────


class TestRequiredOutcomeStore:
    @pytest.mark.asyncio
    async def test_save_and_get(self, store):
        ro = _make_required_outcome()
        await store.save_required_outcome(ro)
        result = await store.get_required_outcome(ro.id, ro.version)
        assert result is not None
        assert result.id == ro.id

    @pytest.mark.asyncio
    async def test_duplicate_raises(self, store):
        ro = _make_required_outcome()
        await store.save_required_outcome(ro)
        with pytest.raises(ValueError, match="already exists"):
            await store.save_required_outcome(ro)

    @pytest.mark.asyncio
    async def test_get_latest(self, store):
        eid = uuid4()
        await store.save_required_outcome(_make_required_outcome(entity_id=eid, version=1))
        await store.save_required_outcome(
            _make_required_outcome(entity_id=eid, version=2, name="v2")
        )
        result = await store.get_latest_required_outcome(eid)
        assert result is not None
        assert result.version == 2

    @pytest.mark.asyncio
    async def test_batch_get(self, store):
        ro1 = _make_required_outcome(name="ro1")
        ro2 = _make_required_outcome(name="ro2")
        await store.save_required_outcome(ro1)
        await store.save_required_outcome(ro2)
        results = await store.get_required_outcomes([(ro1.id, 1), (ro2.id, 1)])
        assert len(results) == 2
