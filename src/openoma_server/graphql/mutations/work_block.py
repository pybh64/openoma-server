from uuid import UUID

import strawberry
from strawberry.types import Info

from openoma_server.auth.context import CurrentUser
from openoma_server.graphql.inputs.work_block import CreateWorkBlockInput, UpdateWorkBlockInput
from openoma_server.graphql.resolvers import work_block_to_gql
from openoma_server.graphql.types.work_block import WorkBlockType
from openoma_server.services import work_block as wb_service


def _get_user(info: Info) -> CurrentUser:
    ctx = info.context
    if hasattr(ctx, "user"):
        return ctx.user
    if hasattr(ctx, "request") and hasattr(ctx.request, "state"):
        return getattr(ctx.request.state, "user", CurrentUser())
    return CurrentUser()


@strawberry.type
class WorkBlockMutation:
    @strawberry.mutation
    async def create_work_block(self, info: Info, input: CreateWorkBlockInput) -> WorkBlockType:
        user = _get_user(info)
        doc = await wb_service.create_work_block(input, user)
        return work_block_to_gql(doc)

    @strawberry.mutation
    async def update_work_block(
        self, info: Info, id: UUID, input: UpdateWorkBlockInput
    ) -> WorkBlockType:
        user = _get_user(info)
        doc = await wb_service.update_work_block(id, input, user)
        return work_block_to_gql(doc)
