from uuid import UUID

import strawberry

from openoma_server.graphql.types.common import JSON


@strawberry.input
class ExecutorInfoInput:
    type: str  # "human", "agent", "system", "team"
    identifier: str
    metadata: JSON | None = None


@strawberry.input
class ExecutionOutcomeInput:
    value: JSON | None = None
    metadata: JSON | None = None


@strawberry.input
class CreateBlockExecutionInput:
    work_block_id: UUID
    work_block_version: int
    node_reference_id: UUID
    flow_execution_id: UUID | None = None


@strawberry.input
class CreateFlowExecutionInput:
    flow_id: UUID
    flow_version: int
    contract_execution_id: UUID | None = None


@strawberry.input
class CreateContractExecutionInput:
    contract_id: UUID
    contract_version: int
