"""Canvas layout service — CRUD for visual node/edge positioning."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from openoma_server.graphql.inputs.canvas_layout import (
    EdgeLayoutInput,
    NodePositionInput,
    SaveCanvasLayoutInput,
)
from openoma_server.models.canvas_layout import (
    CanvasLayoutDoc,
    EdgeLayoutDoc,
    NodePositionDoc,
)


def _convert_node_position(n: NodePositionInput) -> NodePositionDoc:
    return NodePositionDoc(
        node_reference_id=n.node_reference_id,
        x=n.x,
        y=n.y,
        width=n.width,
        height=n.height,
        metadata=n.metadata or {},
    )


def _convert_edge_layout(e: EdgeLayoutInput) -> EdgeLayoutDoc:
    return EdgeLayoutDoc(
        source_id=e.source_id,
        target_id=e.target_id,
        bend_points=e.bend_points or [],
        label_position=e.label_position,
        metadata=e.metadata or {},
    )


async def save_canvas_layout(
    flow_id: UUID,
    flow_version: int,
    input: SaveCanvasLayoutInput,
    user: str | None = None,
) -> CanvasLayoutDoc:
    """Upsert a canvas layout for the given flow_id + flow_version."""
    existing = await CanvasLayoutDoc.find_one(
        CanvasLayoutDoc.flow_id == flow_id,
        CanvasLayoutDoc.flow_version == flow_version,
    )

    if existing is not None:
        if input.node_positions is not None:
            existing.node_positions = [_convert_node_position(n) for n in input.node_positions]
        if input.edge_layouts is not None:
            existing.edge_layouts = [_convert_edge_layout(e) for e in input.edge_layouts]
        if input.viewport is not None:
            existing.viewport = input.viewport
        existing.updated_at = datetime.now(UTC)
        existing.updated_by = user
        await existing.save()
        return existing

    doc = CanvasLayoutDoc(
        flow_id=flow_id,
        flow_version=flow_version,
        node_positions=[_convert_node_position(n) for n in (input.node_positions or [])],
        edge_layouts=[_convert_edge_layout(e) for e in (input.edge_layouts or [])],
        viewport=input.viewport or {},
        updated_at=datetime.now(UTC),
        updated_by=user,
    )
    await doc.insert()
    return doc


async def get_canvas_layout(flow_id: UUID, flow_version: int) -> CanvasLayoutDoc | None:
    """Retrieve a canvas layout by flow_id + flow_version."""
    return await CanvasLayoutDoc.find_one(
        CanvasLayoutDoc.flow_id == flow_id,
        CanvasLayoutDoc.flow_version == flow_version,
    )


async def delete_canvas_layout(flow_id: UUID, flow_version: int) -> bool:
    """Delete a canvas layout. Returns True if a document was deleted."""
    doc = await CanvasLayoutDoc.find_one(
        CanvasLayoutDoc.flow_id == flow_id,
        CanvasLayoutDoc.flow_version == flow_version,
    )
    if doc is None:
        return False
    await doc.delete()
    return True
