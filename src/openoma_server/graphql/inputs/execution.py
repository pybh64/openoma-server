"""Strawberry input types for execution mutations."""

from uuid import UUID

import strawberry


@strawberry.input
class StartBlockExecutionInput:
    node_reference_id: UUID
    work_block_id: UUID
    work_block_version: int
    flow_execution_id: UUID | None = None
    executor_type: str = "system"
    executor_id: str = ""


@strawberry.input
class StartFlowExecutionInput:
    flow_id: UUID
    flow_version: int
    contract_execution_id: UUID | None = None


@strawberry.input
class StartContractExecutionInput:
    contract_id: UUID
    contract_version: int


@strawberry.input
class EmitExecutionEventInput:
    execution_id: UUID
    event_type: str
    executor_type: str | None = None
    executor_id: str | None = None
    payload: strawberry.scalars.JSON | None = None
    metadata: strawberry.scalars.JSON | None = None
