from __future__ import annotations

from datetime import datetime
from uuid import UUID

import strawberry

from openoma_server.graphql.types.common import JSON


@strawberry.type
class NodePositionType:
    node_reference_id: UUID
    x: float
    y: float
    width: float | None
    height: float | None
    metadata: JSON


@strawberry.type
class EdgeLayoutType:
    source_id: UUID | None
    target_id: UUID
    bend_points: list[JSON]
    label_position: JSON | None
    metadata: JSON


@strawberry.type
class CanvasLayoutType:
    flow_id: UUID
    flow_version: int
    node_positions: list[NodePositionType]
    edge_layouts: list[EdgeLayoutType]
    viewport: JSON
    updated_at: datetime
    updated_by: str | None
