from uuid import UUID

import strawberry
from strawberry.types import Info

from openoma_server.auth.context import CurrentUser
from openoma_server.graphql.inputs.contract import (
    CreateContractInput,
    CreateRequiredOutcomeInput,
    UpdateContractInput,
    UpdateRequiredOutcomeInput,
)
from openoma_server.graphql.resolvers import contract_to_gql, required_outcome_to_gql
from openoma_server.graphql.types.contract import ContractType, RequiredOutcomeType
from openoma_server.services import contract as contract_service
from openoma_server.services import required_outcome as ro_service


def _get_user(info: Info) -> CurrentUser:
    ctx = info.context
    if hasattr(ctx, "user"):
        return ctx.user
    if hasattr(ctx, "request") and hasattr(ctx.request, "state"):
        return getattr(ctx.request.state, "user", CurrentUser())
    return CurrentUser()


@strawberry.type
class ContractMutation:
    @strawberry.mutation
    async def create_contract(self, info: Info, input: CreateContractInput) -> ContractType:
        user = _get_user(info)
        doc = await contract_service.create_contract(input, user)
        return contract_to_gql(doc)

    @strawberry.mutation
    async def update_contract(
        self, info: Info, id: UUID, input: UpdateContractInput
    ) -> ContractType:
        user = _get_user(info)
        doc = await contract_service.update_contract(id, input, user)
        return contract_to_gql(doc)

    @strawberry.mutation
    async def create_required_outcome(
        self, info: Info, input: CreateRequiredOutcomeInput
    ) -> RequiredOutcomeType:
        user = _get_user(info)
        doc = await ro_service.create_required_outcome(input, user)
        return required_outcome_to_gql(doc)

    @strawberry.mutation
    async def update_required_outcome(
        self, info: Info, id: UUID, input: UpdateRequiredOutcomeInput
    ) -> RequiredOutcomeType:
        user = _get_user(info)
        doc = await ro_service.update_required_outcome(id, input, user)
        return required_outcome_to_gql(doc)
