from uuid import UUID

import strawberry

from openoma_server.graphql.inputs.filters import (
    ContractFilter,
    ContractOrderBy,
    OrderDirection,
)
from openoma_server.graphql.resolvers import contract_to_gql, required_outcome_to_gql
from openoma_server.graphql.types.contract import ContractType, RequiredOutcomeType
from openoma_server.graphql.types.pagination import (
    ContractConnection,
    ContractEdge,
    PageInfo,
    decode_cursor,
    encode_cursor,
)
from openoma_server.services import contract as contract_service
from openoma_server.services import required_outcome as ro_service
from openoma_server.store.definition_store import MongoDefinitionStore


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
    async def contracts_connection(
        self,
        first: int = 50,
        after: str | None = None,
        filter: ContractFilter | None = None,
        order_by: ContractOrderBy = ContractOrderBy.CREATED_AT,
        order_direction: OrderDirection = OrderDirection.DESC,
    ) -> ContractConnection:
        store = MongoDefinitionStore()
        filter_dict = {}
        if filter:
            if filter.name is not None:
                filter_dict["name"] = filter.name
            if filter.created_by is not None:
                filter_dict["created_by"] = filter.created_by
            if filter.created_after is not None:
                filter_dict["created_after"] = filter.created_after
            if filter.created_before is not None:
                filter_dict["created_before"] = filter.created_before

        after_cursor = decode_cursor(after) if after else None
        sort_dir = -1 if order_direction == OrderDirection.DESC else 1

        docs, total_count, has_next = await store.list_contracts_connection(
            first=first,
            after=after_cursor,
            filter=filter_dict or None,
            sort_field=order_by.value,
            sort_direction=sort_dir,
        )

        edges = [
            ContractEdge(
                node=contract_to_gql(doc),
                cursor=encode_cursor(
                    getattr(doc, order_by.value).isoformat()
                    if order_by == ContractOrderBy.CREATED_AT
                    else str(getattr(doc, order_by.value)),
                    str(doc.entity_id),
                ),
            )
            for doc in docs
        ]

        return ContractConnection(
            edges=edges,
            page_info=PageInfo(
                has_next_page=has_next,
                has_previous_page=after is not None,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            total_count=total_count,
        )

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
