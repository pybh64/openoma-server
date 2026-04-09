"""Tests for WorkBlock service operations."""

import pytest

from openoma_server.auth.context import AuthContext
from openoma_server.services import work_block as work_block_svc


@pytest.fixture
def auth():
    return AuthContext(user_id="test-user", tenant_id="test-tenant", attributes={"roles": ["admin"]})


class TestWorkBlockService:
    @pytest.mark.asyncio
    async def test_create_and_get(self, init_db, auth):
        block = await work_block_svc.create_work_block(
            name="Test Block",
            description="A test work block",
            inputs=[{"name": "input1", "description": "first input"}],
            outputs=[{"name": "output1", "description": "first output"}],
            execution_hints=["sql-access"],
            auth=auth,
        )
        assert block.name == "Test Block"
        assert block.version == 1
        assert len(block.inputs) == 1
        assert block.inputs[0].name == "input1"

        retrieved = await work_block_svc.get_work_block(block.id, auth=auth)
        assert retrieved is not None
        assert retrieved.id == block.id
        assert retrieved.name == "Test Block"

    @pytest.mark.asyncio
    async def test_update_creates_new_version(self, init_db, auth):
        block = await work_block_svc.create_work_block(
            name="Original", auth=auth
        )
        updated = await work_block_svc.update_work_block(
            block.id, name="Updated", auth=auth
        )
        assert updated is not None
        assert updated.version == 2
        assert updated.name == "Updated"
        assert updated.id == block.id

        # Original version still exists
        original = await work_block_svc.get_work_block(block.id, version=1, auth=auth)
        assert original is not None
        assert original.name == "Original"

    @pytest.mark.asyncio
    async def test_list_work_blocks(self, init_db, auth):
        await work_block_svc.create_work_block(name="Alpha", auth=auth)
        await work_block_svc.create_work_block(name="Beta", auth=auth)

        blocks = await work_block_svc.list_work_blocks(auth=auth, latest_only=False)
        assert len(blocks) >= 2

    @pytest.mark.asyncio
    async def test_delete(self, init_db, auth):
        block = await work_block_svc.create_work_block(name="ToDelete", auth=auth)
        count = await work_block_svc.delete_work_block(block.id, auth=auth)
        assert count == 1

        retrieved = await work_block_svc.get_work_block(block.id, auth=auth)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, init_db, auth):
        other_auth = AuthContext(
            user_id="other-user", tenant_id="other-tenant", attributes={"roles": ["admin"]}
        )
        block = await work_block_svc.create_work_block(name="Isolated", auth=auth)

        # Other tenant cannot see it
        retrieved = await work_block_svc.get_work_block(block.id, auth=other_auth)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_versions(self, init_db, auth):
        block = await work_block_svc.create_work_block(name="V1", auth=auth)
        await work_block_svc.update_work_block(block.id, name="V2", auth=auth)
        await work_block_svc.update_work_block(block.id, name="V3", auth=auth)

        versions = await work_block_svc.get_work_block_versions(block.id, auth=auth)
        assert len(versions) == 3
        assert versions[0].version == 1
        assert versions[2].version == 3
