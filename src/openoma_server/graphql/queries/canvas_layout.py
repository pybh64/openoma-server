from __future__ import annotations

from uuid import UUID

import strawberry

from openoma_server.graphql.resolvers import canvas_layout_to_gql
from openoma_server.graphql.types.canvas_layout import CanvasLayoutType
from openoma_server.services import canvas_layout as canvas_layout_service


@strawberry.type
class CanvasLayoutQuery:
    @strawberry.field
    async def canvas_layout(
        self, flow_id: UUID, flow_version: int
    ) -> CanvasLayoutType | None:
        doc = await canvas_layout_service.get_canvas_layout(flow_id, flow_version)
        return canvas_layout_to_gql(doc) if doc else None
