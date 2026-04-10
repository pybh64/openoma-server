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
    block_executions: list[UUID]
    state: str
    created_at: datetime


@strawberry.type
class ContractExecutionType:
    id: UUID
    contract_id: UUID
    contract_version: int
    flow_executions: list[UUID]
    sub_contract_executions: list[UUID]
    assessment_executions: list[AssessmentResultType]
    state: str
    created_at: datetime
