"""Tests for the Canvas Layout service layer."""

from uuid import uuid4

import pytest

from openoma_server.graphql.inputs.canvas_layout import (
    EdgeLayoutInput,
    NodePositionInput,
    SaveCanvasLayoutInput,
)
from openoma_server.services.canvas_layout import (
    delete_canvas_layout,
    get_canvas_layout,
    save_canvas_layout,
)

pytestmark = pytest.mark.asyncio

FLOW_ID = uuid4()
FLOW_VERSION = 1


async def test_save_and_get_canvas_layout():
    node_id = uuid4()
    target_id = uuid4()

    input_data = SaveCanvasLayoutInput(
        node_positions=[
            NodePositionInput(
                node_reference_id=node_id,
                x=100.0,
                y=200.0,
                width=180.0,
                height=60.0,
                metadata={"color": "blue"},
            )
        ],
        edge_layouts=[
            EdgeLayoutInput(
                source_id=node_id,
                target_id=target_id,
                bend_points=[{"x": 150, "y": 250}],
                label_position={"x": 125, "y": 225},
                metadata={"style": "dashed"},
            )
        ],
        viewport={"x": 0, "y": 0, "zoom": 1.0},
    )

    doc = await save_canvas_layout(FLOW_ID, FLOW_VERSION, input_data, user="tester")

    assert doc.flow_id == FLOW_ID
    assert doc.flow_version == FLOW_VERSION
    assert len(doc.node_positions) == 1
    assert doc.node_positions[0].node_reference_id == node_id
    assert doc.node_positions[0].x == 100.0
    assert doc.node_positions[0].y == 200.0
    assert doc.node_positions[0].width == 180.0
    assert doc.node_positions[0].metadata == {"color": "blue"}
    assert len(doc.edge_layouts) == 1
    assert doc.edge_layouts[0].target_id == target_id
    assert doc.edge_layouts[0].bend_points == [{"x": 150, "y": 250}]
    assert doc.viewport == {"x": 0, "y": 0, "zoom": 1.0}
    assert doc.updated_by == "tester"

    # Retrieve and verify
    fetched = await get_canvas_layout(FLOW_ID, FLOW_VERSION)
    assert fetched is not None
    assert fetched.flow_id == FLOW_ID
    assert len(fetched.node_positions) == 1


async def test_save_canvas_layout_upsert():
    flow_id = uuid4()
    node_id = uuid4()

    # Create initial layout
    initial = SaveCanvasLayoutInput(
        node_positions=[
            NodePositionInput(node_reference_id=node_id, x=10.0, y=20.0),
        ],
        viewport={"x": 0, "y": 0, "zoom": 1.0},
    )
    doc1 = await save_canvas_layout(flow_id, 1, initial, user="user1")
    assert len(doc1.node_positions) == 1
    assert doc1.node_positions[0].x == 10.0

    # Upsert with new positions
    new_node_id = uuid4()
    updated = SaveCanvasLayoutInput(
        node_positions=[
            NodePositionInput(node_reference_id=node_id, x=50.0, y=60.0),
            NodePositionInput(node_reference_id=new_node_id, x=100.0, y=200.0),
        ],
        viewport={"x": 10, "y": 20, "zoom": 1.5},
    )
    doc2 = await save_canvas_layout(flow_id, 1, updated, user="user2")

    assert doc2.id == doc1.id  # same document
    assert len(doc2.node_positions) == 2
    assert doc2.node_positions[0].x == 50.0
    assert doc2.viewport == {"x": 10, "y": 20, "zoom": 1.5}
    assert doc2.updated_by == "user2"


async def test_save_canvas_layout_upsert_partial():
    """Upsert with None fields preserves existing data."""
    flow_id = uuid4()
    node_id = uuid4()

    initial = SaveCanvasLayoutInput(
        node_positions=[
            NodePositionInput(node_reference_id=node_id, x=10.0, y=20.0),
        ],
        viewport={"x": 0, "y": 0, "zoom": 1.0},
    )
    await save_canvas_layout(flow_id, 1, initial, user="user1")

    # Upsert with only viewport change
    partial = SaveCanvasLayoutInput(viewport={"x": 5, "y": 5, "zoom": 2.0})
    doc = await save_canvas_layout(flow_id, 1, partial, user="user2")

    assert len(doc.node_positions) == 1  # preserved
    assert doc.node_positions[0].x == 10.0
    assert doc.viewport == {"x": 5, "y": 5, "zoom": 2.0}


async def test_get_nonexistent_layout_returns_none():
    result = await get_canvas_layout(uuid4(), 999)
    assert result is None


async def test_delete_canvas_layout():
    flow_id = uuid4()
    input_data = SaveCanvasLayoutInput(viewport={"x": 0, "y": 0, "zoom": 1.0})
    await save_canvas_layout(flow_id, 1, input_data)

    deleted = await delete_canvas_layout(flow_id, 1)
    assert deleted is True

    # Verify it's gone
    result = await get_canvas_layout(flow_id, 1)
    assert result is None


async def test_delete_nonexistent_returns_false():
    result = await delete_canvas_layout(uuid4(), 999)
    assert result is False
