"""Tests for the FlowDraft service layer."""

from uuid import uuid4

import pytest

from openoma_server.auth.context import CurrentUser
from openoma_server.graphql.inputs.flow import (
    CreateFlowInput,
    EdgeInput,
    NodeReferenceInput,
)
from openoma_server.graphql.inputs.work_block import CreateWorkBlockInput
from openoma_server.services.flow import create_flow
from openoma_server.services.flow_draft import (
    add_edge_to_draft,
    add_node_to_draft,
    create_blank_draft,
    create_draft_from_flow,
    discard_draft,
    get_draft,
    list_drafts,
    publish_draft,
    remove_edge_from_draft,
    remove_node_from_draft,
    update_node_in_draft,
    update_node_positions,
    update_viewport,
)
from openoma_server.services.work_block import create_work_block

pytestmark = pytest.mark.asyncio

USER = CurrentUser(id="test-user", email="test@example.com")


async def _make_work_block(name: str = "Test Block"):
    return await create_work_block(CreateWorkBlockInput(name=name), USER)


async def _make_flow_with_nodes():
    """Create a flow with two nodes and one edge for forking tests."""
    wb1 = await _make_work_block("Block A")
    wb2 = await _make_work_block("Block B")
    n1 = uuid4()
    n2 = uuid4()
    doc = await create_flow(
        CreateFlowInput(
            name="Base Flow",
            description="A test flow",
            nodes=[
                NodeReferenceInput(id=n1, target_id=wb1.entity_id, target_version=1),
                NodeReferenceInput(id=n2, target_id=wb2.entity_id, target_version=1),
            ],
            edges=[EdgeInput(source_id=n1, target_id=n2)],
        ),
        USER,
    )
    return doc, n1, n2, wb1, wb2


# ── Lifecycle tests ───────────────────────────────────────────────


async def test_create_blank_draft():
    draft = await create_blank_draft("My Draft", USER)
    assert draft.name == "My Draft"
    assert draft.base_flow_id is None
    assert draft.base_flow_version is None
    assert draft.nodes == []
    assert draft.edges == []
    assert draft.created_by == USER.display_name


async def test_create_draft_from_flow():
    flow_doc, n1, n2, _, _ = await _make_flow_with_nodes()

    draft = await create_draft_from_flow(flow_doc.entity_id, flow_doc.version, USER)
    assert draft.base_flow_id == flow_doc.entity_id
    assert draft.base_flow_version == flow_doc.version
    assert draft.name == flow_doc.name
    assert len(draft.nodes) == 2
    assert len(draft.edges) == 1


async def test_discard_draft():
    draft = await create_blank_draft("To Discard", USER)
    assert await discard_draft(draft.draft_id) is True
    assert await get_draft(draft.draft_id) is None


async def test_discard_nonexistent_draft():
    assert await discard_draft(uuid4()) is False


# ── Granular node operations ─────────────────────────────────────


async def test_add_node_to_draft():
    wb = await _make_work_block()
    draft = await create_blank_draft("Node Draft", USER)

    node_input = NodeReferenceInput(
        target_id=wb.entity_id, target_version=wb.version, alias="step1"
    )
    updated = await add_node_to_draft(draft.draft_id, node_input)
    assert len(updated.nodes) == 1
    assert updated.nodes[0].alias == "step1"
    assert updated.nodes[0].target_id == wb.entity_id
    # id should be auto-generated
    assert updated.nodes[0].id is not None


async def test_add_node_with_position():
    wb = await _make_work_block()
    draft = await create_blank_draft("Pos Draft", USER)

    node_input = NodeReferenceInput(target_id=wb.entity_id, target_version=1)
    position = {"node_reference_id": str(uuid4()), "x": 100.0, "y": 200.0}
    updated = await add_node_to_draft(draft.draft_id, node_input, position)
    assert len(updated.node_positions) == 1
    assert updated.node_positions[0]["x"] == 100.0


async def test_remove_node_from_draft():
    wb1 = await _make_work_block("Block 1")
    wb2 = await _make_work_block("Block 2")
    draft = await create_blank_draft("Remove Node", USER)

    n1_input = NodeReferenceInput(target_id=wb1.entity_id, target_version=1)
    draft = await add_node_to_draft(draft.draft_id, n1_input)
    n1_id = draft.nodes[0].id

    n2_input = NodeReferenceInput(target_id=wb2.entity_id, target_version=1)
    draft = await add_node_to_draft(draft.draft_id, n2_input)
    n2_id = draft.nodes[1].id

    # Add edge between the two nodes
    edge_input = EdgeInput(source_id=n1_id, target_id=n2_id)
    draft = await add_edge_to_draft(draft.draft_id, edge_input)
    assert len(draft.edges) == 1

    # Remove first node — edge should also be removed
    draft = await remove_node_from_draft(draft.draft_id, n1_id)
    assert len(draft.nodes) == 1
    assert draft.nodes[0].id == n2_id
    assert len(draft.edges) == 0


async def test_update_node_in_draft():
    wb = await _make_work_block()
    draft = await create_blank_draft("Update Node", USER)

    node_input = NodeReferenceInput(target_id=wb.entity_id, target_version=1, alias="old")
    draft = await add_node_to_draft(draft.draft_id, node_input)
    node_id = draft.nodes[0].id

    draft = await update_node_in_draft(
        draft.draft_id, node_id, alias="new-alias", metadata={"key": "val"}
    )
    assert draft.nodes[0].alias == "new-alias"
    assert draft.nodes[0].metadata == {"key": "val"}


async def test_update_node_not_found():
    draft = await create_blank_draft("Empty", USER)
    with pytest.raises(ValueError, match="not found in draft"):
        await update_node_in_draft(draft.draft_id, uuid4(), alias="x")


# ── Granular edge operations ─────────────────────────────────────


async def test_add_edge_to_draft():
    wb = await _make_work_block()
    draft = await create_blank_draft("Edge Draft", USER)

    n1_input = NodeReferenceInput(target_id=wb.entity_id, target_version=1)
    draft = await add_node_to_draft(draft.draft_id, n1_input)
    n1_id = draft.nodes[0].id

    n2_input = NodeReferenceInput(target_id=wb.entity_id, target_version=1)
    draft = await add_node_to_draft(draft.draft_id, n2_input)
    n2_id = draft.nodes[1].id

    edge_input = EdgeInput(source_id=n1_id, target_id=n2_id)
    draft = await add_edge_to_draft(draft.draft_id, edge_input)
    assert len(draft.edges) == 1
    assert draft.edges[0].source_id == n1_id
    assert draft.edges[0].target_id == n2_id


async def test_add_entry_edge_to_draft():
    """Entry edges have source_id=None."""
    wb = await _make_work_block()
    draft = await create_blank_draft("Entry Edge", USER)

    n_input = NodeReferenceInput(target_id=wb.entity_id, target_version=1)
    draft = await add_node_to_draft(draft.draft_id, n_input)
    n_id = draft.nodes[0].id

    edge_input = EdgeInput(target_id=n_id)
    draft = await add_edge_to_draft(draft.draft_id, edge_input)
    assert draft.edges[0].source_id is None


async def test_add_edge_invalid_target():
    draft = await create_blank_draft("Bad Edge", USER)
    with pytest.raises(ValueError, match="target_id"):
        await add_edge_to_draft(draft.draft_id, EdgeInput(target_id=uuid4()))


async def test_add_edge_invalid_source():
    wb = await _make_work_block()
    draft = await create_blank_draft("Bad Source", USER)

    n_input = NodeReferenceInput(target_id=wb.entity_id, target_version=1)
    draft = await add_node_to_draft(draft.draft_id, n_input)
    n_id = draft.nodes[0].id

    with pytest.raises(ValueError, match="source_id"):
        await add_edge_to_draft(
            draft.draft_id, EdgeInput(source_id=uuid4(), target_id=n_id)
        )


async def test_remove_edge_from_draft():
    wb = await _make_work_block()
    draft = await create_blank_draft("Remove Edge", USER)

    n1_input = NodeReferenceInput(target_id=wb.entity_id, target_version=1)
    draft = await add_node_to_draft(draft.draft_id, n1_input)
    n1_id = draft.nodes[0].id

    n2_input = NodeReferenceInput(target_id=wb.entity_id, target_version=1)
    draft = await add_node_to_draft(draft.draft_id, n2_input)
    n2_id = draft.nodes[1].id

    draft = await add_edge_to_draft(draft.draft_id, EdgeInput(source_id=n1_id, target_id=n2_id))
    assert len(draft.edges) == 1

    draft = await remove_edge_from_draft(draft.draft_id, n1_id, n2_id)
    assert len(draft.edges) == 0


# ── Layout operations ────────────────────────────────────────────


async def test_update_node_positions():
    draft = await create_blank_draft("Positions", USER)
    positions = [
        {"node_reference_id": str(uuid4()), "x": 10.0, "y": 20.0},
        {"node_reference_id": str(uuid4()), "x": 30.0, "y": 40.0},
    ]
    draft = await update_node_positions(draft.draft_id, positions)
    assert len(draft.node_positions) == 2
    assert draft.node_positions[0]["x"] == 10.0
    assert draft.node_positions[1]["y"] == 40.0


async def test_update_viewport():
    draft = await create_blank_draft("Viewport", USER)
    viewport = {"x": 0.0, "y": 0.0, "zoom": 1.5}
    draft = await update_viewport(draft.draft_id, viewport)
    assert draft.viewport["zoom"] == 1.5


# ── Publish tests ────────────────────────────────────────────────


async def test_publish_draft_new_flow():
    """Publishing a blank draft creates a new flow (version 1)."""
    wb = await _make_work_block()
    draft = await create_blank_draft("New Flow Draft", USER)

    n_input = NodeReferenceInput(target_id=wb.entity_id, target_version=1)
    draft = await add_node_to_draft(draft.draft_id, n_input)
    n_id = draft.nodes[0].id

    # Add entry edge to satisfy validate_flow
    draft = await add_edge_to_draft(draft.draft_id, EdgeInput(target_id=n_id))

    flow_doc = await publish_draft(draft.draft_id, USER)
    assert flow_doc.version == 1
    assert flow_doc.name == "New Flow Draft"
    assert len(flow_doc.nodes) == 1

    # Draft should be deleted
    assert await get_draft(draft.draft_id) is None


async def test_publish_draft_existing_flow():
    """Publishing a forked draft creates a new version of the base flow."""
    flow_doc, n1, n2, _, _ = await _make_flow_with_nodes()
    draft = await create_draft_from_flow(flow_doc.entity_id, flow_doc.version, USER)

    published = await publish_draft(draft.draft_id, USER)
    assert published.entity_id == flow_doc.entity_id
    assert published.version == flow_doc.version + 1
    assert len(published.nodes) == 2

    # Draft should be deleted
    assert await get_draft(draft.draft_id) is None


async def test_publish_nonexistent_draft():
    with pytest.raises(ValueError, match="not found"):
        await publish_draft(uuid4(), USER)


# ── List tests ───────────────────────────────────────────────────


async def test_list_drafts():
    await create_blank_draft("Draft 1", USER)
    await create_blank_draft("Draft 2", USER)

    results = await list_drafts()
    assert len(results) >= 2


async def test_list_drafts_by_base_flow():
    flow_doc, _, _, _, _ = await _make_flow_with_nodes()
    await create_draft_from_flow(flow_doc.entity_id, flow_doc.version, USER)
    await create_blank_draft("Unrelated", USER)

    results = await list_drafts(base_flow_id=flow_doc.entity_id)
    assert len(results) >= 1
    assert all(d.base_flow_id == flow_doc.entity_id for d in results)
