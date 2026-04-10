from uuid import UUID

import strawberry

from openoma_server.graphql.inputs.filters import (
    FlowFilter,
    FlowOrderBy,
    OrderDirection,
)
from openoma_server.graphql.resolvers import flow_to_gql
from openoma_server.graphql.types.flow import FlowType
from openoma_server.graphql.types.pagination import (
    FlowConnection,
    FlowEdge,
    PageInfo,
    decode_cursor,
    encode_cursor,
)
from openoma_server.services import flow as flow_service
from openoma_server.store.definition_store import MongoDefinitionStore


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

    @strawberry.field
    async def flows_connection(
        self,
        first: int = 50,
        after: str | None = None,
        filter: FlowFilter | None = None,
        order_by: FlowOrderBy = FlowOrderBy.CREATED_AT,
        order_direction: OrderDirection = OrderDirection.DESC,
    ) -> FlowConnection:
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

        docs, total_count, has_next = await store.list_flows_connection(
            first=first,
            after=after_cursor,
            filter=filter_dict or None,
            sort_field=order_by.value,
            sort_direction=sort_dir,
        )

        edges = [
            FlowEdge(
                node=flow_to_gql(doc),
                cursor=encode_cursor(
                    getattr(doc, order_by.value).isoformat()
                    if order_by == FlowOrderBy.CREATED_AT
                    else str(getattr(doc, order_by.value)),
                    str(doc.entity_id),
                ),
            )
            for doc in docs
        ]

        return FlowConnection(
            edges=edges,
            page_info=PageInfo(
                has_next_page=has_next,
                has_previous_page=after is not None,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            total_count=total_count,
        )
