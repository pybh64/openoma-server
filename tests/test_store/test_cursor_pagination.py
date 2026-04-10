"""Tests for cursor pagination in definition and execution stores."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from openoma.core.contract import Contract
from openoma.core.flow import Flow, NodeReference
from openoma.core.work_block import WorkBlock

from openoma_server.graphql.types.pagination import decode_cursor, encode_cursor
from openoma_server.models.execution import BlockExecutionDoc
from openoma_server.store.definition_store import MongoDefinitionStore
from openoma_server.store.execution_store import MongoExecutionStore

# ── Cursor utilities ──────────────────────────────────────────────


class TestCursorEncoding:
    def test_roundtrip(self):
        sort_val = "2024-01-15T10:30:00+00:00"
        eid = str(uuid4())
        cursor = encode_cursor(sort_val, eid)
        decoded_sort, decoded_eid = decode_cursor(cursor)
        assert decoded_sort == sort_val
        assert decoded_eid == eid

    def test_cursor_is_url_safe(self):
        cursor = encode_cursor("2024-01-01T00:00:00+00:00", str(uuid4()))
        assert "+" not in cursor or cursor.replace("+", "").isalnum  # url-safe base64


# ── Helpers ───────────────────────────────────────────────────────


def _make_work_block(
    *,
    name: str = "test-block",
    version: int = 1,
    entity_id=None,
    created_at=None,
    created_by=None,
):
    return WorkBlock(
        id=entity_id or uuid4(),
        version=version,
        name=name,
        description=f"{name} description",
        created_at=created_at or datetime.now(UTC),
        created_by=created_by,
    )


def _make_flow(
    *,
    name: str = "test-flow",
    version: int = 1,
    entity_id=None,
    created_at=None,
    created_by=None,
):
    return Flow(
        id=entity_id or uuid4(),
        version=version,
        name=name,
        description=f"{name} description",
        created_at=created_at or datetime.now(UTC),
        created_by=created_by,
        nodes=[NodeReference(id=uuid4(), target_id=uuid4(), target_version=1)],
        edges=[],
    )


def _make_contract(
    *,
    name: str = "test-contract",
    version: int = 1,
    entity_id=None,
    created_at=None,
    created_by=None,
):
    return Contract(
        id=entity_id or uuid4(),
        version=version,
        name=name,
        description=f"{name} description",
        created_at=created_at or datetime.now(UTC),
        created_by=created_by,
        owners=[],
        work_flows=[],
        sub_contracts=[],
        required_outcomes=[],
    )


# ── Definition store connection tests ─────────────────────────────


@pytest.fixture
def def_store():
    return MongoDefinitionStore()


@pytest.fixture
def exec_store():
    return MongoExecutionStore()


class TestWorkBlockConnection:
    @pytest.mark.asyncio
    async def test_empty_connection(self, def_store):
        docs, total, has_next = await def_store.list_work_blocks_connection(first=10)
        assert docs == []
        assert total == 0
        assert has_next is False

    @pytest.mark.asyncio
    async def test_basic_pagination(self, def_store):
        base = datetime(2024, 1, 1, tzinfo=UTC)
        for i in range(5):
            wb = _make_work_block(
                name=f"block-{i}",
                created_at=base + timedelta(hours=i),
            )
            await def_store.save_work_block(wb)

        docs, total, has_next = await def_store.list_work_blocks_connection(first=3)
        assert total == 5
        assert len(docs) == 3
        assert has_next is True

    @pytest.mark.asyncio
    async def test_no_more_pages(self, def_store):
        wb = _make_work_block(name="only-one")
        await def_store.save_work_block(wb)

        docs, total, has_next = await def_store.list_work_blocks_connection(first=10)
        assert total == 1
        assert len(docs) == 1
        assert has_next is False

    @pytest.mark.asyncio
    async def test_latest_version_only(self, def_store):
        eid = uuid4()
        base = datetime(2024, 1, 1, tzinfo=UTC)
        await def_store.save_work_block(
            _make_work_block(entity_id=eid, version=1, name="v1", created_at=base)
        )
        await def_store.save_work_block(
            _make_work_block(
                entity_id=eid, version=2, name="v2",
                created_at=base + timedelta(hours=1),
            )
        )

        docs, total, has_next = await def_store.list_work_blocks_connection(first=10)
        assert total == 1
        assert len(docs) == 1
        assert docs[0].version == 2
        assert docs[0].name == "v2"

    @pytest.mark.asyncio
    async def test_name_filter(self, def_store):
        base = datetime(2024, 1, 1, tzinfo=UTC)
        await def_store.save_work_block(
            _make_work_block(name="Alpha Block", created_at=base)
        )
        await def_store.save_work_block(
            _make_work_block(name="Beta Block", created_at=base + timedelta(hours=1))
        )
        await def_store.save_work_block(
            _make_work_block(name="Gamma", created_at=base + timedelta(hours=2))
        )

        docs, total, _ = await def_store.list_work_blocks_connection(
            first=10, filter={"name": "block"}
        )
        assert total == 2
        assert len(docs) == 2

    @pytest.mark.asyncio
    async def test_created_by_filter(self, def_store):
        base = datetime(2024, 1, 1, tzinfo=UTC)
        await def_store.save_work_block(
            _make_work_block(name="a", created_by="alice", created_at=base)
        )
        await def_store.save_work_block(
            _make_work_block(name="b", created_by="bob", created_at=base + timedelta(hours=1))
        )

        docs, total, _ = await def_store.list_work_blocks_connection(
            first=10, filter={"created_by": "alice"}
        )
        assert total == 1
        assert docs[0].created_by == "alice"

    @pytest.mark.asyncio
    async def test_date_range_filter(self, def_store):
        base = datetime(2024, 1, 1, tzinfo=UTC)
        await def_store.save_work_block(
            _make_work_block(name="old", created_at=base)
        )
        await def_store.save_work_block(
            _make_work_block(name="mid", created_at=base + timedelta(days=5))
        )
        await def_store.save_work_block(
            _make_work_block(name="new", created_at=base + timedelta(days=10))
        )

        docs, total, _ = await def_store.list_work_blocks_connection(
            first=10,
            filter={
                "created_after": base + timedelta(days=3),
                "created_before": base + timedelta(days=7),
            },
        )
        assert total == 1
        assert docs[0].name == "mid"

    @pytest.mark.asyncio
    async def test_ascending_sort(self, def_store):
        base = datetime(2024, 1, 1, tzinfo=UTC)
        for i in range(3):
            await def_store.save_work_block(
                _make_work_block(name=f"block-{i}", created_at=base + timedelta(hours=i))
            )

        docs, _, _ = await def_store.list_work_blocks_connection(
            first=10, sort_direction=1
        )
        dates = [d.created_at for d in docs]
        assert dates == sorted(dates)


class TestFlowConnection:
    @pytest.mark.asyncio
    async def test_empty_connection(self, def_store):
        docs, total, has_next = await def_store.list_flows_connection(first=10)
        assert docs == []
        assert total == 0
        assert has_next is False

    @pytest.mark.asyncio
    async def test_basic_pagination(self, def_store):
        base = datetime(2024, 1, 1, tzinfo=UTC)
        for i in range(4):
            await def_store.save_flow(
                _make_flow(name=f"flow-{i}", created_at=base + timedelta(hours=i))
            )

        docs, total, has_next = await def_store.list_flows_connection(first=2)
        assert total == 4
        assert len(docs) == 2
        assert has_next is True

    @pytest.mark.asyncio
    async def test_name_filter(self, def_store):
        base = datetime(2024, 1, 1, tzinfo=UTC)
        await def_store.save_flow(
            _make_flow(name="Deploy Flow", created_at=base)
        )
        await def_store.save_flow(
            _make_flow(name="Build Flow", created_at=base + timedelta(hours=1))
        )
        await def_store.save_flow(
            _make_flow(name="Cleanup", created_at=base + timedelta(hours=2))
        )

        docs, total, _ = await def_store.list_flows_connection(
            first=10, filter={"name": "flow"}
        )
        assert total == 2


class TestContractConnection:
    @pytest.mark.asyncio
    async def test_empty_connection(self, def_store):
        docs, total, has_next = await def_store.list_contracts_connection(first=10)
        assert docs == []
        assert total == 0
        assert has_next is False

    @pytest.mark.asyncio
    async def test_basic_pagination(self, def_store):
        base = datetime(2024, 1, 1, tzinfo=UTC)
        for i in range(4):
            await def_store.save_contract(
                _make_contract(name=f"contract-{i}", created_at=base + timedelta(hours=i))
            )

        docs, total, has_next = await def_store.list_contracts_connection(first=2)
        assert total == 4
        assert len(docs) == 2
        assert has_next is True


# ── Execution store connection tests ──────────────────────────────


class TestBlockExecutionConnection:
    @pytest.mark.asyncio
    async def test_empty_connection(self, exec_store):
        docs, total, has_next = await exec_store.list_block_executions_connection(first=10)
        assert docs == []
        assert total == 0
        assert has_next is False

    @pytest.mark.asyncio
    async def test_basic_pagination(self, exec_store):
        base = datetime(2024, 1, 1, tzinfo=UTC)
        for i in range(5):
            doc = BlockExecutionDoc(
                execution_id=uuid4(),
                node_reference_id=uuid4(),
                work_block_id=uuid4(),
                work_block_version=1,
                state="pending",
                created_at=base + timedelta(hours=i),
            )
            await doc.insert()

        docs, total, has_next = await exec_store.list_block_executions_connection(first=3)
        assert total == 5
        assert len(docs) == 3
        assert has_next is True

    @pytest.mark.asyncio
    async def test_state_filter(self, exec_store):
        base = datetime(2024, 1, 1, tzinfo=UTC)
        for i, state in enumerate(["pending", "running", "pending"]):
            doc = BlockExecutionDoc(
                execution_id=uuid4(),
                node_reference_id=uuid4(),
                work_block_id=uuid4(),
                work_block_version=1,
                state=state,
                created_at=base + timedelta(hours=i),
            )
            await doc.insert()

        docs, total, _ = await exec_store.list_block_executions_connection(
            first=10, filter={"state": "pending"}
        )
        assert total == 2
        assert all(d.state == "pending" for d in docs)

    @pytest.mark.asyncio
    async def test_no_more_pages(self, exec_store):
        doc = BlockExecutionDoc(
            execution_id=uuid4(),
            node_reference_id=uuid4(),
            work_block_id=uuid4(),
            work_block_version=1,
            state="pending",
            created_at=datetime.now(UTC),
        )
        await doc.insert()

        docs, total, has_next = await exec_store.list_block_executions_connection(first=10)
        assert total == 1
        assert len(docs) == 1
        assert has_next is False
