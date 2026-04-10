"""Tests for the WorkBlock service layer."""

import pytest

from openoma_server.auth.context import CurrentUser
from openoma_server.graphql.inputs.work_block import (
    CreateWorkBlockInput,
    ExpectedOutcomeInput,
    PortDescriptorInput,
    UpdateWorkBlockInput,
)
from openoma_server.services.work_block import (
    create_work_block,
    get_work_block,
    list_work_blocks,
    update_work_block,
)

pytestmark = pytest.mark.asyncio

USER = CurrentUser(id="test-user", email="test@example.com")


async def test_create_minimal_work_block():
    doc = await create_work_block(CreateWorkBlockInput(name="Review Document"), USER)
    assert doc.name == "Review Document"
    assert doc.version == 1
    assert doc.entity_id is not None
    assert doc.created_by == "test@example.com"


async def test_create_work_block_with_ports():
    doc = await create_work_block(
        CreateWorkBlockInput(
            name="Transform Data",
            description="Transforms input data",
            inputs=[
                PortDescriptorInput(name="raw_data", description="Raw input"),
                PortDescriptorInput(name="config", required=False),
            ],
            outputs=[PortDescriptorInput(name="result")],
            execution_hints=["manual", "requires_review"],
        ),
        USER,
    )
    assert doc.name == "Transform Data"
    assert len(doc.inputs) == 2
    assert len(doc.outputs) == 1
    assert doc.inputs[0].name == "raw_data"
    assert doc.inputs[1].required is False
    assert doc.execution_hints == ["manual", "requires_review"]


async def test_create_work_block_with_expected_outcome():
    doc = await create_work_block(
        CreateWorkBlockInput(
            name="Validate Entry",
            expected_outcome=ExpectedOutcomeInput(
                name="validation_result",
                description="Whether the entry is valid",
                schema_def={"type": "boolean"},
            ),
        ),
        USER,
    )
    assert doc.expected_outcome is not None
    assert doc.expected_outcome.name == "validation_result"
    assert doc.expected_outcome.schema_def == {"type": "boolean"}


async def test_create_work_block_with_metadata():
    doc = await create_work_block(
        CreateWorkBlockInput(
            name="Canvas Block",
            metadata={"position": {"x": 100, "y": 200}, "color": "blue"},
        ),
        USER,
    )
    assert doc.metadata["position"] == {"x": 100, "y": 200}
    assert doc.metadata["color"] == "blue"


async def test_update_work_block_creates_new_version():
    doc = await create_work_block(
        CreateWorkBlockInput(name="Original Name", description="v1"), USER
    )
    updated = await update_work_block(
        doc.entity_id,
        UpdateWorkBlockInput(name="Updated Name", description="v2"),
        USER,
    )
    assert updated.entity_id == doc.entity_id
    assert updated.version == 2
    assert updated.name == "Updated Name"
    assert updated.description == "v2"


async def test_update_work_block_partial():
    doc = await create_work_block(
        CreateWorkBlockInput(name="Keep Me", description="Original desc"),
        USER,
    )
    updated = await update_work_block(
        doc.entity_id,
        UpdateWorkBlockInput(description="New desc"),
        USER,
    )
    assert updated.name == "Keep Me"  # unchanged
    assert updated.description == "New desc"


async def test_update_nonexistent_raises():
    from uuid import uuid4

    with pytest.raises(ValueError, match="not found"):
        await update_work_block(uuid4(), UpdateWorkBlockInput(name="x"), USER)


async def test_get_work_block_latest():
    doc = await create_work_block(CreateWorkBlockInput(name="Versioned"), USER)
    await update_work_block(doc.entity_id, UpdateWorkBlockInput(name="Versioned v2"), USER)

    latest = await get_work_block(doc.entity_id)
    assert latest is not None
    assert latest.version == 2
    assert latest.name == "Versioned v2"


async def test_get_work_block_specific_version():
    doc = await create_work_block(CreateWorkBlockInput(name="V1 Name"), USER)
    await update_work_block(doc.entity_id, UpdateWorkBlockInput(name="V2 Name"), USER)

    v1 = await get_work_block(doc.entity_id, version=1)
    assert v1 is not None
    assert v1.name == "V1 Name"


async def test_get_work_block_not_found():
    from uuid import uuid4

    result = await get_work_block(uuid4())
    assert result is None


async def test_list_work_blocks():
    await create_work_block(CreateWorkBlockInput(name="Alpha"), USER)
    await create_work_block(CreateWorkBlockInput(name="Beta"), USER)
    await create_work_block(CreateWorkBlockInput(name="Gamma"), USER)

    results = await list_work_blocks()
    assert len(results) >= 3


async def test_list_work_blocks_with_name_filter():
    await create_work_block(CreateWorkBlockInput(name="SearchTarget"), USER)
    await create_work_block(CreateWorkBlockInput(name="Other Block"), USER)

    results = await list_work_blocks(name="SearchTarget")
    assert len(results) >= 1
    assert all("SearchTarget" in r.name for r in results)


async def test_list_work_blocks_returns_latest_version_only():
    doc = await create_work_block(CreateWorkBlockInput(name="MultiVersion"), USER)
    await update_work_block(doc.entity_id, UpdateWorkBlockInput(name="MultiVersion v2"), USER)

    results = await list_work_blocks(name="MultiVersion")
    matching = [r for r in results if r.entity_id == doc.entity_id]
    assert len(matching) == 1
    assert matching[0].version == 2


async def test_roundtrip_to_core():
    """Verify Beanie doc → openoma core model → back works correctly."""
    doc = await create_work_block(
        CreateWorkBlockInput(
            name="Roundtrip",
            inputs=[PortDescriptorInput(name="data", description="input data")],
            outputs=[PortDescriptorInput(name="result")],
            expected_outcome=ExpectedOutcomeInput(name="ok"),
            metadata={"key": "value"},
        ),
        USER,
    )
    core = doc.to_core()
    assert core.name == "Roundtrip"
    assert core.id == doc.entity_id
    assert len(core.inputs) == 1
    assert core.inputs[0].name == "data"
    assert core.expected_outcome is not None
    assert core.metadata["key"] == "value"
