"""GraphQL queries for flow drafts."""

from uuid import UUID

import strawberry

from openoma_server.graphql.resolvers import flow_draft_to_gql
from openoma_server.graphql.types.flow_draft import FlowDraftType
from openoma_server.services import flow_draft as draft_service


@strawberry.type
class FlowDraftQuery:
    @strawberry.field
    async def flow_draft(self, draft_id: UUID) -> FlowDraftType | None:
        doc = await draft_service.get_draft(draft_id)
        return flow_draft_to_gql(doc) if doc else None

    @strawberry.field
    async def flow_drafts(
        self,
        base_flow_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FlowDraftType]:
        docs = await draft_service.list_drafts(
            base_flow_id=base_flow_id, limit=limit, offset=offset
        )
        return [flow_draft_to_gql(d) for d in docs]
