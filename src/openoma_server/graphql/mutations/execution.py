from uuid import UUID

import strawberry
from openoma.execution.types import ExecutionOutcome, ExecutorInfo
from strawberry.types import Info

from openoma_server.auth.context import CurrentUser
from openoma_server.graphql.inputs.execution import (
    CreateBlockExecutionInput,
    CreateContractExecutionInput,
    CreateFlowExecutionInput,
    ExecutionOutcomeInput,
    ExecutorInfoInput,
)
from openoma_server.graphql.resolvers import (
    block_execution_to_gql,
    contract_execution_to_gql,
    flow_execution_to_gql,
)
from openoma_server.graphql.types.execution import (
    BlockExecutionType,
    ContractExecutionType,
    FlowExecutionType,
)
from openoma_server.services import execution as exec_service


def _get_user(info: Info) -> CurrentUser:
    ctx = info.context
    if hasattr(ctx, "user"):
        return ctx.user
    if hasattr(ctx, "request") and hasattr(ctx.request, "state"):
        return getattr(ctx.request.state, "user", CurrentUser())
    return CurrentUser()


def _to_executor_info(inp: ExecutorInfoInput) -> ExecutorInfo:
    return ExecutorInfo(
        type=inp.type,
        identifier=inp.identifier,
        metadata=inp.metadata or {},
    )


def _to_execution_outcome(inp: ExecutionOutcomeInput) -> ExecutionOutcome:
    return ExecutionOutcome(value=inp.value, metadata=inp.metadata or {})


@strawberry.type
class ExecutionMutation:
    # ── Block Execution ────────────────────────────────────────────

    @strawberry.mutation
    async def create_block_execution(
        self, info: Info, input: CreateBlockExecutionInput
    ) -> BlockExecutionType:
        user = _get_user(info)
        doc = await exec_service.create_block_execution(
            work_block_id=input.work_block_id,
            work_block_version=input.work_block_version,
            node_reference_id=input.node_reference_id,
            flow_execution_id=input.flow_execution_id,
            user=user,
        )
        return block_execution_to_gql(doc)

    @strawberry.mutation
    async def assign_executor_to_block(
        self, info: Info, execution_id: UUID, executor: ExecutorInfoInput
    ) -> BlockExecutionType:
        doc = await exec_service.assign_executor_to_block(execution_id, _to_executor_info(executor))
        return block_execution_to_gql(doc)

    @strawberry.mutation
    async def start_block_execution(self, info: Info, execution_id: UUID) -> BlockExecutionType:
        doc = await exec_service.start_block_execution(execution_id)
        return block_execution_to_gql(doc)

    @strawberry.mutation
    async def produce_block_outcome(
        self, info: Info, execution_id: UUID, outcome: ExecutionOutcomeInput
    ) -> BlockExecutionType:
        doc = await exec_service.produce_block_outcome(execution_id, _to_execution_outcome(outcome))
        return block_execution_to_gql(doc)

    @strawberry.mutation
    async def complete_block_execution(self, info: Info, execution_id: UUID) -> BlockExecutionType:
        doc = await exec_service.complete_block_execution(execution_id)
        return block_execution_to_gql(doc)

    @strawberry.mutation
    async def fail_block_execution(
        self, info: Info, execution_id: UUID, metadata: strawberry.scalars.JSON | None = None
    ) -> BlockExecutionType:
        doc = await exec_service.fail_block_execution(execution_id, metadata=metadata)
        return block_execution_to_gql(doc)

    @strawberry.mutation
    async def cancel_block_execution(self, info: Info, execution_id: UUID) -> BlockExecutionType:
        doc = await exec_service.cancel_block_execution(execution_id)
        return block_execution_to_gql(doc)

    # ── Flow Execution ─────────────────────────────────────────────

    @strawberry.mutation
    async def create_flow_execution(
        self, info: Info, input: CreateFlowExecutionInput
    ) -> FlowExecutionType:
        user = _get_user(info)
        doc = await exec_service.create_flow_execution(
            flow_id=input.flow_id,
            flow_version=input.flow_version,
            contract_execution_id=input.contract_execution_id,
            user=user,
        )
        return flow_execution_to_gql(doc)

    @strawberry.mutation
    async def add_block_to_flow_execution(
        self, info: Info, flow_execution_id: UUID, block_execution_id: UUID
    ) -> FlowExecutionType:
        doc = await exec_service.add_block_to_flow_execution(flow_execution_id, block_execution_id)
        return flow_execution_to_gql(doc)

    @strawberry.mutation
    async def refresh_flow_state(self, info: Info, flow_execution_id: UUID) -> FlowExecutionType:
        doc = await exec_service.refresh_flow_state(flow_execution_id)
        return flow_execution_to_gql(doc)

    # ── Contract Execution ─────────────────────────────────────────

    @strawberry.mutation
    async def create_contract_execution(
        self, info: Info, input: CreateContractExecutionInput
    ) -> ContractExecutionType:
        user = _get_user(info)
        doc = await exec_service.create_contract_execution(
            contract_id=input.contract_id,
            contract_version=input.contract_version,
            user=user,
        )
        return contract_execution_to_gql(doc)

    @strawberry.mutation
    async def add_flow_to_contract_execution(
        self, info: Info, contract_execution_id: UUID, flow_execution_id: UUID
    ) -> ContractExecutionType:
        doc = await exec_service.add_flow_to_contract_execution(
            contract_execution_id, flow_execution_id
        )
        return contract_execution_to_gql(doc)

    @strawberry.mutation
    async def refresh_contract_state(
        self, info: Info, contract_execution_id: UUID
    ) -> ContractExecutionType:
        doc = await exec_service.refresh_contract_state(contract_execution_id)
        return contract_execution_to_gql(doc)
