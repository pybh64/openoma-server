from uuid import UUID

import strawberry

from openoma_server.graphql.resolvers import contract_to_gql, required_outcome_to_gql
from openoma_server.graphql.types.contract import ContractType, RequiredOutcomeType
from openoma_server.services import contract as contract_service
from openoma_server.services import required_outcome as ro_service


@strawberry.type
class ContractQuery:
    @strawberry.field
    async def contract(self, id: UUID, version: int | None = None) -> ContractType | None:
        doc = await contract_service.get_contract(id, version)
        return contract_to_gql(doc) if doc else None

    @strawberry.field
    async def contracts(
        self,
        name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ContractType]:
        docs = await contract_service.list_contracts(name=name, limit=limit, offset=offset)
        return [contract_to_gql(d) for d in docs]

    @strawberry.field
    async def required_outcome(
        self, id: UUID, version: int | None = None
    ) -> RequiredOutcomeType | None:
        doc = await ro_service.get_required_outcome(id, version)
        return required_outcome_to_gql(doc) if doc else None

    @strawberry.field
    async def required_outcomes(
        self,
        name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[RequiredOutcomeType]:
        docs = await ro_service.list_required_outcomes(name=name, limit=limit, offset=offset)
        return [required_outcome_to_gql(d) for d in docs]
