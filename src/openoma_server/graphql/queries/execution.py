from uuid import UUID

import strawberry

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
from openoma_server.services import execution as exec_service


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
    async def execution_events(self, execution_id: UUID) -> list[ExecutionEventType]:
        docs = await exec_service.get_events(execution_id)
        return [execution_event_to_gql(d) for d in docs]
