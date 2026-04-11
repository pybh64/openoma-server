"""Tests for the Flow service layer."""

from uuid import uuid4

import pytest

from openoma_server.auth.context import CurrentUser
from openoma_server.graphql.inputs.flow import (
    ConditionInput,
    CreateFlowInput,
    EdgeInput,
    NodeReferenceInput,
    PortMappingInput,
    UpdateFlowInput,
)
from openoma_server.graphql.inputs.work_block import (
    CreateWorkBlockInput,
    ExpectedOutcomeInput,
)
from openoma_server.services.flow import (
    create_flow,
    get_flow,
    list_flows,
    update_flow,
)
from openoma_server.services.work_block import create_work_block

pytestmark = pytest.mark.asyncio

USER = CurrentUser(id="test-user", email="test@example.com")


async def _make_work_block(name: str = "Test Block"):
    return await create_work_block(CreateWorkBlockInput(name=name), USER)


async def test_create_empty_flow():
    doc = await create_flow(CreateFlowInput(name="Empty Flow"), USER)
    assert doc.name == "Empty Flow"
    assert doc.version == 1
    assert doc.nodes == []
    assert doc.edges == []


async def test_create_flow_with_nodes():
    wb = await _make_work_block()
    node_id = uuid4()

    doc = await create_flow(
        CreateFlowInput(
            name="Simple Flow",
            nodes=[
                NodeReferenceInput(
                    id=node_id,
                    target_id=wb.entity_id,
                    target_version=wb.version,
                    alias="step1",
                    execution_schedule="cron: 0 9 * * 1-5",
                    metadata={"position": {"x": 100, "y": 200}},
                )
            ],
        ),
        USER,
    )
    assert len(doc.nodes) == 1
    assert doc.nodes[0].id == node_id
    assert doc.nodes[0].target_id == wb.entity_id
    assert doc.nodes[0].alias == "step1"
    assert doc.nodes[0].execution_schedule == "cron: 0 9 * * 1-5"
    assert doc.nodes[0].metadata["position"] == {"x": 100, "y": 200}


async def test_create_flow_with_edges():
    wb1 = await _make_work_block("Block A")
    wb2 = await _make_work_block("Block B")
    n1 = uuid4()
    n2 = uuid4()

    doc = await create_flow(
        CreateFlowInput(
            name="Two Step Flow",
            nodes=[
                NodeReferenceInput(id=n1, target_id=wb1.entity_id, target_version=1),
                NodeReferenceInput(id=n2, target_id=wb2.entity_id, target_version=1),
            ],
            edges=[
                EdgeInput(
                    source_id=n1,
                    target_id=n2,
                    port_mappings=[PortMappingInput(source_port="output", target_port="input")],
                )
            ],
        ),
        USER,
    )
    assert len(doc.edges) == 1
    assert doc.edges[0].source_id == n1
    assert doc.edges[0].target_id == n2
    assert len(doc.edges[0].port_mappings) == 1


async def test_create_flow_with_conditional_edge():
    wb = await _make_work_block()
    n1 = uuid4()
    n2 = uuid4()

    doc = await create_flow(
        CreateFlowInput(
            name="Conditional Flow",
            nodes=[
                NodeReferenceInput(id=n1, target_id=wb.entity_id, target_version=1),
                NodeReferenceInput(id=n2, target_id=wb.entity_id, target_version=1),
            ],
            edges=[
                EdgeInput(
                    source_id=n1,
                    target_id=n2,
                    condition=ConditionInput(
                        description="If approved",
                        predicate={"field": "status", "equals": "approved"},
                    ),
                )
            ],
        ),
        USER,
    )
    assert doc.edges[0].condition is not None
    assert doc.edges[0].condition.description == "If approved"


async def test_create_flow_with_entry_edge():
    """Entry edges have no source (None source_id)."""
    wb = await _make_work_block()
    n1 = uuid4()

    doc = await create_flow(
        CreateFlowInput(
            name="Entry Flow",
            nodes=[
                NodeReferenceInput(id=n1, target_id=wb.entity_id, target_version=1),
            ],
            edges=[EdgeInput(target_id=n1)],
        ),
        USER,
    )
    assert doc.edges[0].source_id is None
    assert doc.edges[0].target_id == n1


async def test_create_flow_with_expected_outcome():
    doc = await create_flow(
        CreateFlowInput(
            name="Outcome Flow",
            expected_outcome=ExpectedOutcomeInput(name="completion", description="Flow completed"),
        ),
        USER,
    )
    assert doc.expected_outcome is not None
    assert doc.expected_outcome.name == "completion"


async def test_update_flow_creates_new_version():
    doc = await create_flow(CreateFlowInput(name="V1 Flow"), USER)
    updated = await update_flow(
        doc.entity_id,
        UpdateFlowInput(name="V2 Flow", description="updated"),
        USER,
    )
    assert updated.entity_id == doc.entity_id
    assert updated.version == 2
    assert updated.name == "V2 Flow"


async def test_update_flow_partial():
    doc = await create_flow(CreateFlowInput(name="Keep Name", description="Original"), USER)
    updated = await update_flow(
        doc.entity_id,
        UpdateFlowInput(description="Changed"),
        USER,
    )
    assert updated.name == "Keep Name"
    assert updated.description == "Changed"


async def test_update_nonexistent_flow_raises():
    with pytest.raises(ValueError, match="not found"):
        await update_flow(uuid4(), UpdateFlowInput(name="x"), USER)


async def test_get_flow_latest():
    doc = await create_flow(CreateFlowInput(name="GetMe"), USER)
    await update_flow(doc.entity_id, UpdateFlowInput(name="GetMe v2"), USER)

    latest = await get_flow(doc.entity_id)
    assert latest is not None
    assert latest.version == 2


async def test_get_flow_specific_version():
    doc = await create_flow(CreateFlowInput(name="Version1"), USER)
    await update_flow(doc.entity_id, UpdateFlowInput(name="Version2"), USER)

    v1 = await get_flow(doc.entity_id, version=1)
    assert v1 is not None
    assert v1.name == "Version1"


async def test_get_flow_not_found():
    result = await get_flow(uuid4())
    assert result is None


async def test_list_flows():
    await create_flow(CreateFlowInput(name="Flow A"), USER)
    await create_flow(CreateFlowInput(name="Flow B"), USER)

    results = await list_flows()
    assert len(results) >= 2


async def test_list_flows_name_filter():
    await create_flow(CreateFlowInput(name="UniqueFlowName"), USER)

    results = await list_flows(name="UniqueFlowName")
    assert len(results) >= 1
    assert all("UniqueFlowName" in r.name for r in results)


async def test_list_flows_returns_latest_only():
    doc = await create_flow(CreateFlowInput(name="LatestOnly"), USER)
    await update_flow(doc.entity_id, UpdateFlowInput(name="LatestOnly v2"), USER)

    results = await list_flows(name="LatestOnly")
    matching = [r for r in results if r.entity_id == doc.entity_id]
    assert len(matching) == 1
    assert matching[0].version == 2


async def test_flow_roundtrip_to_core():
    wb = await _make_work_block()
    n1 = uuid4()
    n2 = uuid4()

    doc = await create_flow(
        CreateFlowInput(
            name="Roundtrip",
            nodes=[
                NodeReferenceInput(
                    id=n1,
                    target_id=wb.entity_id,
                    target_version=1,
                    execution_schedule="run independently when urgent work arrives",
                ),
                NodeReferenceInput(id=n2, target_id=wb.entity_id, target_version=1),
            ],
            edges=[EdgeInput(source_id=n1, target_id=n2)],
            metadata={"canvas": True},
        ),
        USER,
    )
    core = doc.to_core()
    assert core.name == "Roundtrip"
    assert len(core.nodes) == 2
    assert len(core.edges) == 1
    assert core.nodes[0].execution_schedule == "run independently when urgent work arrives"
    assert core.metadata["canvas"] is True


async def test_canvas_position_metadata_preserved():
    """Verify that canvas position metadata survives create → get cycle."""
    wb = await _make_work_block()
    node_id = uuid4()
    position = {"x": 350, "y": 120}

    created = await create_flow(
        CreateFlowInput(
            name="Canvas Flow",
            nodes=[
                NodeReferenceInput(
                    id=node_id,
                    target_id=wb.entity_id,
                    target_version=1,
                    metadata={"position": position},
                )
            ],
        ),
        USER,
    )

    fetched = await get_flow(created.entity_id)
    assert fetched is not None
    assert fetched.nodes[0].metadata["position"] == position
