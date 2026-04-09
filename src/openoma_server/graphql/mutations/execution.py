"""Mutation resolvers for execution lifecycle operations."""

import strawberry

from openoma_server.auth.context import AuthContext
from openoma_server.auth.permissions import CanCreateExecution
from openoma_server.graphql.inputs.execution import (
    EmitExecutionEventInput,
    StartBlockExecutionInput,
    StartContractExecutionInput,
    StartFlowExecutionInput,
)
from openoma_server.graphql.types.execution import (
    BlockExecutionType,
    ContractExecutionType,
    ExecutionEventType as ExecutionEventGQLType,
    FlowExecutionType,
    block_execution_to_type,
    contract_execution_to_type,
    event_to_type,
    flow_execution_to_type,
)
from openoma_server.services import execution as execution_svc


def _get_auth(info: strawberry.Info) -> AuthContext:
    return info.context["auth"]


@strawberry.type
class ExecutionMutation:
    @strawberry.mutation(permission_classes=[CanCreateExecution])
    async def start_block_execution(
        self, info: strawberry.Info, input: StartBlockExecutionInput
    ) -> BlockExecutionType:
        be = await execution_svc.start_block_execution(
            node_reference_id=input.node_reference_id,
            work_block_id=input.work_block_id,
            work_block_version=input.work_block_version,
            flow_execution_id=input.flow_execution_id,
            executor_type=input.executor_type,
            executor_id=input.executor_id,
            auth=_get_auth(info),
        )
        return block_execution_to_type(be)

    @strawberry.mutation(permission_classes=[CanCreateExecution])
    async def start_flow_execution(
        self, info: strawberry.Info, input: StartFlowExecutionInput
    ) -> FlowExecutionType:
        fe = await execution_svc.start_flow_execution(
            flow_id=input.flow_id,
            flow_version=input.flow_version,
            contract_execution_id=input.contract_execution_id,
            auth=_get_auth(info),
        )
        return flow_execution_to_type(fe)

    @strawberry.mutation(permission_classes=[CanCreateExecution])
    async def start_contract_execution(
        self, info: strawberry.Info, input: StartContractExecutionInput
    ) -> ContractExecutionType:
        ce = await execution_svc.start_contract_execution(
            contract_id=input.contract_id,
            contract_version=input.contract_version,
            auth=_get_auth(info),
        )
        return contract_execution_to_type(ce)

    @strawberry.mutation(permission_classes=[CanCreateExecution])
    async def emit_execution_event(
        self, info: strawberry.Info, input: EmitExecutionEventInput
    ) -> ExecutionEventGQLType:
        event = await execution_svc.emit_execution_event(
            execution_id=input.execution_id,
            event_type=input.event_type,
            executor_type=input.executor_type,
            executor_id=input.executor_id,
            payload=input.payload,
            metadata=input.metadata,
            auth=_get_auth(info),
        )
        return event_to_type(event)
