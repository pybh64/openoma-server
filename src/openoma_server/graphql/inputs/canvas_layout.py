from __future__ import annotations

from uuid import UUID

import strawberry

from openoma_server.graphql.types.common import JSON


@strawberry.input
class NodePositionInput:
    node_reference_id: UUID
    x: float = 0.0
    y: float = 0.0
    width: float | None = None
    height: float | None = None
    metadata: JSON | None = None


@strawberry.input
class EdgeLayoutInput:
    source_id: UUID | None = None
    target_id: UUID = strawberry.UNSET
    bend_points: list[JSON] | None = None
    label_position: JSON | None = None
    metadata: JSON | None = None


@strawberry.input
class SaveCanvasLayoutInput:
    node_positions: list[NodePositionInput] | None = None
    edge_layouts: list[EdgeLayoutInput] | None = None
    viewport: JSON | None = None
