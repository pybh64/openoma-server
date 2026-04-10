from uuid import UUID

import strawberry

from openoma_server.graphql.inputs.filters import (
    BlockExecutionFilter,
    ContractExecutionFilter,
    ExecutionOrderByField,
    FlowExecutionFilter,
    OrderDirection,
)
from openoma_server.graphql.resolvers import (
    block_execution_to_gql,
    contract_execution_to_gql,
    execution_event_to_gql,
    flow_execution_to_gql,
)
from openoma_server.graphql.types.execution import (
    BlockExecutionType,
    ContractExecutionType,
    ExecutionEventType,
    FlowExecutionType,
)
from openoma_server.graphql.types.pagination import (
    BlockExecutionConnection,
    BlockExecutionEdge,
    ContractExecutionConnection,
    ContractExecutionEdge,
    FlowExecutionConnection,
    FlowExecutionEdge,
    PageInfo,
    decode_cursor,
    encode_cursor,
)
from openoma_server.services import execution as exec_service
from openoma_server.store.execution_store import MongoExecutionStore


@strawberry.type
class ExecutionQuery:
    @strawberry.field
    async def block_execution(self, id: UUID) -> BlockExecutionType | None:
        doc = await exec_service.get_block_execution(id)
        return block_execution_to_gql(doc) if doc else None

    @strawberry.field
    async def block_executions(
        self,
        work_block_id: UUID | None = None,
        flow_execution_id: UUID | None = None,
        state: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[BlockExecutionType]:
        docs = await exec_service.list_block_executions(
            work_block_id=work_block_id,
            flow_execution_id=flow_execution_id,
            state=state,
            limit=limit,
            offset=offset,
        )
        return [block_execution_to_gql(d) for d in docs]

    @strawberry.field
    async def block_executions_connection(
        self,
        first: int = 50,
        after: str | None = None,
        filter: BlockExecutionFilter | None = None,
        order_by: ExecutionOrderByField = ExecutionOrderByField.CREATED_AT,
        order_direction: OrderDirection = OrderDirection.DESC,
    ) -> BlockExecutionConnection:
        store = MongoExecutionStore()
        filter_dict = {}
        if filter:
            if filter.work_block_id is not None:
                filter_dict["work_block_id"] = UUID(filter.work_block_id)
            if filter.flow_execution_id is not None:
                filter_dict["flow_execution_id"] = UUID(filter.flow_execution_id)
            if filter.state is not None:
                filter_dict["state"] = filter.state

        after_cursor = decode_cursor(after) if after else None
        sort_dir = -1 if order_direction == OrderDirection.DESC else 1

        docs, total_count, has_next = await store.list_block_executions_connection(
            first=first,
            after=after_cursor,
            filter=filter_dict or None,
            sort_field=order_by.value,
            sort_direction=sort_dir,
        )

        edges = [
            BlockExecutionEdge(
                node=block_execution_to_gql(doc),
                cursor=encode_cursor(doc.created_at.isoformat(), str(doc.execution_id)),
            )
            for doc in docs
        ]

        return BlockExecutionConnection(
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
    async def flow_execution(self, id: UUID) -> FlowExecutionType | None:
        doc = await exec_service.get_flow_execution(id)
        return flow_execution_to_gql(doc) if doc else None

    @strawberry.field
    async def flow_executions(
        self,
        flow_id: UUID | None = None,
        contract_execution_id: UUID | None = None,
        state: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FlowExecutionType]:
        docs = await exec_service.list_flow_executions(
            flow_id=flow_id,
            contract_execution_id=contract_execution_id,
            state=state,
            limit=limit,
            offset=offset,
        )
        return [flow_execution_to_gql(d) for d in docs]

    @strawberry.field
    async def flow_executions_connection(
        self,
        first: int = 50,
        after: str | None = None,
        filter: FlowExecutionFilter | None = None,
        order_by: ExecutionOrderByField = ExecutionOrderByField.CREATED_AT,
        order_direction: OrderDirection = OrderDirection.DESC,
    ) -> FlowExecutionConnection:
        store = MongoExecutionStore()
        filter_dict = {}
        if filter:
            if filter.flow_id is not None:
                filter_dict["flow_id"] = UUID(filter.flow_id)
            if filter.contract_execution_id is not None:
                filter_dict["contract_execution_id"] = UUID(filter.contract_execution_id)
            if filter.state is not None:
                filter_dict["state"] = filter.state

        after_cursor = decode_cursor(after) if after else None
        sort_dir = -1 if order_direction == OrderDirection.DESC else 1

        docs, total_count, has_next = await store.list_flow_executions_connection(
            first=first,
            after=after_cursor,
            filter=filter_dict or None,
            sort_field=order_by.value,
            sort_direction=sort_dir,
        )

        edges = [
            FlowExecutionEdge(
                node=flow_execution_to_gql(doc),
                cursor=encode_cursor(doc.created_at.isoformat(), str(doc.execution_id)),
            )
            for doc in docs
        ]

        return FlowExecutionConnection(
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
    async def contract_execution(self, id: UUID) -> ContractExecutionType | None:
        doc = await exec_service.get_contract_execution(id)
        return contract_execution_to_gql(doc) if doc else None

    @strawberry.field
    async def contract_executions(
        self,
        contract_id: UUID | None = None,
        state: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ContractExecutionType]:
        docs = await exec_service.list_contract_executions(
            contract_id=contract_id,
            state=state,
            limit=limit,
            offset=offset,
        )
        return [contract_execution_to_gql(d) for d in docs]

    @strawberry.field
    async def contract_executions_connection(
        self,
        first: int = 50,
        after: str | None = None,
        filter: ContractExecutionFilter | None = None,
        order_by: ExecutionOrderByField = ExecutionOrderByField.CREATED_AT,
        order_direction: OrderDirection = OrderDirection.DESC,
    ) -> ContractExecutionConnection:
        store = MongoExecutionStore()
        filter_dict = {}
        if filter:
            if filter.contract_id is not None:
                filter_dict["contract_id"] = UUID(filter.contract_id)
            if filter.state is not None:
                filter_dict["state"] = filter.state

        after_cursor = decode_cursor(after) if after else None
        sort_dir = -1 if order_direction == OrderDirection.DESC else 1

        docs, total_count, has_next = await store.list_contract_executions_connection(
            first=first,
            after=after_cursor,
            filter=filter_dict or None,
            sort_field=order_by.value,
            sort_direction=sort_dir,
        )

        edges = [
            ContractExecutionEdge(
                node=contract_execution_to_gql(doc),
                cursor=encode_cursor(doc.created_at.isoformat(), str(doc.execution_id)),
            )
            for doc in docs
        ]

        return ContractExecutionConnection(
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
    async def execution_events(self, execution_id: UUID) -> list[ExecutionEventType]:
        docs = await exec_service.get_events(execution_id)
        return [execution_event_to_gql(d) for d in docs]
