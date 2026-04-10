from uuid import UUID

import strawberry
from strawberry.types import Info

from openoma_server.auth.context import CurrentUser
from openoma_server.graphql.inputs.flow import CreateFlowInput, UpdateFlowInput
from openoma_server.graphql.resolvers import flow_to_gql
from openoma_server.graphql.types.flow import FlowType
from openoma_server.services import flow as flow_service


def _get_user(info: Info) -> CurrentUser:
    ctx = info.context
    if hasattr(ctx, "user"):
        return ctx.user
    if hasattr(ctx, "request") and hasattr(ctx.request, "state"):
        return getattr(ctx.request.state, "user", CurrentUser())
    return CurrentUser()


@strawberry.type
class FlowMutation:
    @strawberry.mutation
    async def create_flow(self, info: Info, input: CreateFlowInput) -> FlowType:
        user = _get_user(info)
        doc = await flow_service.create_flow(input, user)
        return flow_to_gql(doc)

    @strawberry.mutation
    async def update_flow(self, info: Info, id: UUID, input: UpdateFlowInput) -> FlowType:
        user = _get_user(info)
        doc = await flow_service.update_flow(id, input, user)
        return flow_to_gql(doc)
