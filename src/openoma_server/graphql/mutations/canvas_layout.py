from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry.types import Info

from openoma_server.auth.context import CurrentUser
from openoma_server.graphql.inputs.canvas_layout import SaveCanvasLayoutInput
from openoma_server.graphql.resolvers import canvas_layout_to_gql
from openoma_server.graphql.types.canvas_layout import CanvasLayoutType
from openoma_server.services import canvas_layout as canvas_layout_service


def _get_user(info: Info) -> CurrentUser:
    ctx = info.context
    if hasattr(ctx, "user"):
        return ctx.user
    if hasattr(ctx, "request") and hasattr(ctx.request, "state"):
        return getattr(ctx.request.state, "user", CurrentUser())
    return CurrentUser()


@strawberry.type
class CanvasLayoutMutation:
    @strawberry.mutation
    async def save_canvas_layout(
        self,
        info: Info,
        flow_id: UUID,
        flow_version: int,
        input: SaveCanvasLayoutInput,
    ) -> CanvasLayoutType:
        user = _get_user(info)
        doc = await canvas_layout_service.save_canvas_layout(
            flow_id, flow_version, input, user=user.display_name
        )
        return canvas_layout_to_gql(doc)

    @strawberry.mutation
    async def delete_canvas_layout(
        self, info: Info, flow_id: UUID, flow_version: int
    ) -> bool:
        return await canvas_layout_service.delete_canvas_layout(flow_id, flow_version)
