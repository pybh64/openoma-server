from __future__ import annotations

from datetime import datetime
from uuid import UUID

import strawberry

from openoma_server.graphql.types.common import JSON


@strawberry.type
class ExecutorInfoType:
    type: str
    identifier: str
    metadata: JSON


@strawberry.type
class ExecutionOutcomeType:
    value: JSON | None
    metadata: JSON


@strawberry.type
class ExecutionEventType:
    id: UUID
    timestamp: datetime
    execution_id: UUID
    event_type: str
    executor: ExecutorInfoType | None
    outcome: ExecutionOutcomeType | None
    metadata: JSON


@strawberry.type
class AssessmentResultType:
    required_outcome_id: UUID
    assessment_flow_execution_id: UUID
    result: JSON | None


@strawberry.type
class BlockExecutionType:
    id: UUID
    flow_execution_id: UUID | None
    node_reference_id: UUID
    work_block_id: UUID
    work_block_version: int
    state: str
    created_at: datetime


@strawberry.type
class FlowExecutionType:
    id: UUID
    contract_execution_id: UUID | None
    flow_id: UUID
    flow_version: int
    _block_execution_ids: strawberry.Private[list[UUID]]
    state: str
    created_at: datetime

    @strawberry.field
    async def block_executions(self, info: strawberry.Info) -> list[BlockExecutionType]:
        from openoma_server.graphql.resolvers import block_execution_to_gql

        ctx = info.context
        docs = await ctx.block_execution_loader.load_many(self._block_execution_ids)
        return [block_execution_to_gql(doc) for doc in docs if doc is not None]


@strawberry.type
class ContractExecutionType:
    id: UUID
    contract_id: UUID
    contract_version: int
    _flow_execution_ids: strawberry.Private[list[UUID]]
    _sub_contract_execution_ids: strawberry.Private[list[UUID]]
    assessment_executions: list[AssessmentResultType]
    state: str
    created_at: datetime

    @strawberry.field
    async def flow_executions(self, info: strawberry.Info) -> list[FlowExecutionType]:
        from openoma_server.graphql.resolvers import flow_execution_to_gql

        ctx = info.context
        docs = await ctx.flow_execution_loader.load_many(self._flow_execution_ids)
        return [flow_execution_to_gql(doc) for doc in docs if doc is not None]

    @strawberry.field
    async def sub_contract_executions(
        self, info: strawberry.Info
    ) -> list[ContractExecutionType]:
        from openoma_server.graphql.resolvers import contract_execution_to_gql

        ctx = info.context
        docs = await ctx.contract_execution_loader.load_many(
            self._sub_contract_execution_ids
        )
        return [contract_execution_to_gql(doc) for doc in docs if doc is not None]
