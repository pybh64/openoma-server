from uuid import UUID

import strawberry

from openoma_server.graphql.inputs.filters import (
    OrderDirection,
    WorkBlockFilter,
    WorkBlockOrderBy,
)
from openoma_server.graphql.resolvers import work_block_to_gql
from openoma_server.graphql.types.pagination import (
    PageInfo,
    WorkBlockConnection,
    WorkBlockEdge,
    decode_cursor,
    encode_cursor,
)
from openoma_server.graphql.types.work_block import WorkBlockType
from openoma_server.services import work_block as wb_service
from openoma_server.store.definition_store import MongoDefinitionStore


@strawberry.type
class WorkBlockQuery:
    @strawberry.field
    async def work_block(self, id: UUID, version: int | None = None) -> WorkBlockType | None:
        doc = await wb_service.get_work_block(id, version)
        return work_block_to_gql(doc) if doc else None

    @strawberry.field
    async def work_blocks(
        self,
        name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[WorkBlockType]:
        docs = await wb_service.list_work_blocks(name=name, limit=limit, offset=offset)
        return [work_block_to_gql(d) for d in docs]

    @strawberry.field
    async def work_blocks_connection(
        self,
        first: int = 50,
        after: str | None = None,
        filter: WorkBlockFilter | None = None,
        order_by: WorkBlockOrderBy = WorkBlockOrderBy.CREATED_AT,
        order_direction: OrderDirection = OrderDirection.DESC,
    ) -> WorkBlockConnection:
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

        docs, total_count, has_next = await store.list_work_blocks_connection(
            first=first,
            after=after_cursor,
            filter=filter_dict or None,
            sort_field=order_by.value,
            sort_direction=sort_dir,
        )

        edges = [
            WorkBlockEdge(
                node=work_block_to_gql(doc),
                cursor=encode_cursor(
                    getattr(doc, order_by.value).isoformat()
                    if order_by == WorkBlockOrderBy.CREATED_AT
                    else str(getattr(doc, order_by.value)),
                    str(doc.entity_id),
                ),
            )
            for doc in docs
        ]

        return WorkBlockConnection(
            edges=edges,
            page_info=PageInfo(
                has_next_page=has_next,
                has_previous_page=after is not None,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            total_count=total_count,
        )
