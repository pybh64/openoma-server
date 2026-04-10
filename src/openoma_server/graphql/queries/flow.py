from uuid import UUID

import strawberry

from openoma_server.graphql.resolvers import flow_to_gql
from openoma_server.graphql.types.flow import FlowType
from openoma_server.services import flow as flow_service


@strawberry.type
class FlowQuery:
    @strawberry.field
    async def flow(self, id: UUID, version: int | None = None) -> FlowType | None:
        doc = await flow_service.get_flow(id, version)
        return flow_to_gql(doc) if doc else None

    @strawberry.field
    async def flows(
        self,
        name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FlowType]:
        docs = await flow_service.list_flows(name=name, limit=limit, offset=offset)
        return [flow_to_gql(d) for d in docs]
