"""GraphQL mutations for flow drafts."""

from uuid import UUID

import strawberry
from strawberry.types import Info

from openoma_server.auth.context import CurrentUser
from openoma_server.graphql.inputs.canvas_layout import NodePositionInput
from openoma_server.graphql.inputs.flow import EdgeInput, NodeReferenceInput
from openoma_server.graphql.inputs.flow_draft import UpdateNodeInput
from openoma_server.graphql.resolvers import flow_draft_to_gql, flow_to_gql
from openoma_server.graphql.types.common import JSON
from openoma_server.graphql.types.flow import FlowType
from openoma_server.graphql.types.flow_draft import FlowDraftType
from openoma_server.services import flow_draft as draft_service


def _get_user(info: Info) -> CurrentUser:
    ctx = info.context
    if hasattr(ctx, "user"):
        return ctx.user
    if hasattr(ctx, "request") and hasattr(ctx.request, "state"):
        return getattr(ctx.request.state, "user", CurrentUser())
    return CurrentUser()


@strawberry.type
class FlowDraftMutation:
    # ── Lifecycle ─────────────────────────────────────────────────

    @strawberry.mutation
    async def create_flow_draft(
        self, info: Info, flow_id: UUID, flow_version: int
    ) -> FlowDraftType:
        user = _get_user(info)
        doc = await draft_service.create_draft_from_flow(flow_id, flow_version, user)
        return flow_draft_to_gql(doc)

    @strawberry.mutation
    async def create_blank_flow_draft(self, info: Info, name: str) -> FlowDraftType:
        user = _get_user(info)
        doc = await draft_service.create_blank_draft(name, user)
        return flow_draft_to_gql(doc)

    @strawberry.mutation
    async def publish_flow_draft(self, info: Info, draft_id: UUID) -> FlowType:
        user = _get_user(info)
        flow_doc = await draft_service.publish_draft(draft_id, user)
        return flow_to_gql(flow_doc)

    @strawberry.mutation
    async def discard_flow_draft(self, draft_id: UUID) -> bool:
        return await draft_service.discard_draft(draft_id)

    # ── Granular node operations ──────────────────────────────────

    @strawberry.mutation
    async def add_node_to_draft(
        self,
        draft_id: UUID,
        node: NodeReferenceInput,
        position: NodePositionInput | None = None,
    ) -> FlowDraftType:
        pos_dict = None
        if position is not None:
            pos_dict = {
                "node_reference_id": str(position.node_reference_id),
                "x": position.x,
                "y": position.y,
            }
            if position.width is not None:
                pos_dict["width"] = position.width
            if position.height is not None:
                pos_dict["height"] = position.height
            if position.metadata is not None:
                pos_dict["metadata"] = position.metadata
        doc = await draft_service.add_node_to_draft(draft_id, node, pos_dict)
        return flow_draft_to_gql(doc)

    @strawberry.mutation
    async def remove_node_from_draft(
        self, draft_id: UUID, node_reference_id: UUID
    ) -> FlowDraftType:
        doc = await draft_service.remove_node_from_draft(draft_id, node_reference_id)
        return flow_draft_to_gql(doc)

    @strawberry.mutation
    async def update_node_in_draft(
        self, draft_id: UUID, node_reference_id: UUID, input: UpdateNodeInput
    ) -> FlowDraftType:
        doc = await draft_service.update_node_in_draft(
            draft_id,
            node_reference_id,
            target_id=input.target_id,
            target_version=input.target_version,
            alias=input.alias,
            execution_schedule=input.execution_schedule,
            metadata=input.metadata,
        )
        return flow_draft_to_gql(doc)

    # ── Granular edge operations ──────────────────────────────────

    @strawberry.mutation
    async def add_edge_to_draft(self, draft_id: UUID, edge: EdgeInput) -> FlowDraftType:
        doc = await draft_service.add_edge_to_draft(draft_id, edge)
        return flow_draft_to_gql(doc)

    @strawberry.mutation
    async def remove_edge_from_draft(
        self, draft_id: UUID, source_id: UUID | None, target_id: UUID
    ) -> FlowDraftType:
        doc = await draft_service.remove_edge_from_draft(draft_id, source_id, target_id)
        return flow_draft_to_gql(doc)

    @strawberry.mutation
    async def update_edge_in_draft(
        self,
        draft_id: UUID,
        source_id: UUID | None,
        target_id: UUID,
        edge: EdgeInput,
    ) -> FlowDraftType:
        doc = await draft_service.update_edge_in_draft(
            draft_id, source_id, target_id, edge
        )
        return flow_draft_to_gql(doc)

    # ── Layout operations ─────────────────────────────────────────

    @strawberry.mutation
    async def update_node_positions(
        self, draft_id: UUID, positions: list[NodePositionInput]
    ) -> FlowDraftType:
        pos_dicts = []
        for p in positions:
            d: dict = {
                "node_reference_id": str(p.node_reference_id),
                "x": p.x,
                "y": p.y,
            }
            if p.width is not None:
                d["width"] = p.width
            if p.height is not None:
                d["height"] = p.height
            if p.metadata is not None:
                d["metadata"] = p.metadata
            pos_dicts.append(d)
        doc = await draft_service.update_node_positions(draft_id, pos_dicts)
        return flow_draft_to_gql(doc)

    @strawberry.mutation
    async def update_viewport(self, draft_id: UUID, viewport: JSON) -> FlowDraftType:
        doc = await draft_service.update_viewport(draft_id, viewport)
        return flow_draft_to_gql(doc)
