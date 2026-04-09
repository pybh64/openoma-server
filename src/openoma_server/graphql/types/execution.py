"""Strawberry GraphQL types for openoma execution entities."""

from datetime import datetime
from enum import Enum
from typing import Any

import strawberry


@strawberry.enum
class ExecutionStateEnum(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@strawberry.enum
class ExecutionEventTypeEnum(Enum):
    CREATED = "created"
    EXECUTOR_ASSIGNED = "executor_assigned"
    EXECUTOR_RELEASED = "executor_released"
    STARTED = "started"
    PROGRESS = "progress"
    OUTCOME_PRODUCED = "outcome_produced"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@strawberry.type
class ExecutorInfoType:
    type: str
    identifier: str
    metadata: strawberry.scalars.JSON | None = None


@strawberry.type
class ExecutionEventType:
    id: strawberry.ID
    timestamp: datetime
    execution_id: strawberry.ID
    event_type: ExecutionEventTypeEnum
    executor: ExecutorInfoType | None = None
    payload: strawberry.scalars.JSON | None = None
    metadata: strawberry.scalars.JSON | None = None


@strawberry.type
class BlockExecutionType:
    id: strawberry.ID
    node_reference_id: strawberry.ID
    work_block_id: strawberry.ID
    work_block_version: int
    state: ExecutionStateEnum
    events: list[ExecutionEventType]


@strawberry.type
class FlowExecutionType:
    id: strawberry.ID
    flow_id: strawberry.ID
    flow_version: int
    block_execution_ids: list[strawberry.ID]
    state: ExecutionStateEnum
    events: list[ExecutionEventType]


@strawberry.type
class ContractExecutionType:
    id: strawberry.ID
    contract_id: strawberry.ID
    contract_version: int
    flow_execution_ids: list[strawberry.ID]
    sub_contract_execution_ids: list[strawberry.ID]
    state: ExecutionStateEnum
    events: list[ExecutionEventType]


@strawberry.type
class BlockExecutionSummaryType:
    """Lightweight block execution info without full event replay."""

    execution_id: strawberry.ID
    node_reference_id: strawberry.ID
    work_block_id: strawberry.ID
    work_block_version: int
    flow_execution_id: strawberry.ID | None = None
    created_at: datetime | None = None


# --- Conversion helpers ---


def event_to_type(event: Any) -> ExecutionEventType:
    executor = None
    if event.executor:
        executor = ExecutorInfoType(
            type=event.executor.type,
            identifier=event.executor.identifier,
            metadata=event.executor.metadata or None,
        )
    return ExecutionEventType(
        id=strawberry.ID(str(event.id)),
        timestamp=event.timestamp,
        execution_id=strawberry.ID(str(event.execution_id)),
        event_type=ExecutionEventTypeEnum(event.event_type.value),
        executor=executor,
        payload=event.payload,
        metadata=event.metadata or None,
    )


def block_execution_to_type(be: Any) -> BlockExecutionType:
    return BlockExecutionType(
        id=strawberry.ID(str(be.id)),
        node_reference_id=strawberry.ID(str(be.node_reference_id)),
        work_block_id=strawberry.ID(str(be.work_block_id)),
        work_block_version=be.work_block_version,
        state=ExecutionStateEnum(be.state.value),
        events=[event_to_type(e) for e in be.events],
    )


def flow_execution_to_type(fe: Any) -> FlowExecutionType:
    return FlowExecutionType(
        id=strawberry.ID(str(fe.id)),
        flow_id=strawberry.ID(str(fe.flow_id)),
        flow_version=fe.flow_version,
        block_execution_ids=[strawberry.ID(str(bid)) for bid in fe.block_executions],
        state=ExecutionStateEnum(fe.state.value) if hasattr(fe, "state") else ExecutionStateEnum.PENDING,
        events=[event_to_type(e) for e in fe.events],
    )


def contract_execution_to_type(ce: Any) -> ContractExecutionType:
    return ContractExecutionType(
        id=strawberry.ID(str(ce.id)),
        contract_id=strawberry.ID(str(ce.contract_id)),
        contract_version=ce.contract_version,
        flow_execution_ids=[strawberry.ID(str(fid)) for fid in ce.flow_executions],
        sub_contract_execution_ids=[
            strawberry.ID(str(sid)) for sid in ce.sub_contract_executions
        ],
        state=ExecutionStateEnum(ce.state.value) if hasattr(ce, "state") else ExecutionStateEnum.PENDING,
        events=[event_to_type(e) for e in ce.events],
    )
