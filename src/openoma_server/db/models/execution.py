"""Beanie document models for openoma execution entities."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from beanie import Document
from pydantic import Field


class ExecutionEventDocument(Document):
    """Persistent representation of an openoma ExecutionEvent."""

    event_id: UUID
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    execution_id: UUID
    event_type: str  # ExecutionEventType value
    executor: dict | None = None  # ExecutorInfo as dict
    payload: Any | None = None
    metadata: dict = Field(default_factory=dict)
    tenant_id: str

    class Settings:
        name = "execution_events"
        indexes = [
            [("execution_id", 1), ("timestamp", 1)],
            [("tenant_id", 1)],
            [("event_type", 1), ("tenant_id", 1)],
        ]


class BlockExecutionDocument(Document):
    """Persistent representation of an openoma BlockExecution."""

    execution_id: UUID
    node_reference_id: UUID
    work_block_id: UUID
    work_block_version: int
    flow_execution_id: UUID | None = None
    tenant_id: str

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "block_executions"
        indexes = [
            [("execution_id", 1), ("tenant_id", 1)],
            [("flow_execution_id", 1), ("tenant_id", 1)],
            [("tenant_id", 1)],
        ]


class FlowExecutionDocument(Document):
    """Persistent representation of an openoma FlowExecution."""

    execution_id: UUID
    flow_id: UUID
    flow_version: int
    block_execution_ids: list[UUID] = Field(default_factory=list)
    contract_execution_id: UUID | None = None
    tenant_id: str

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "flow_executions"
        indexes = [
            [("execution_id", 1), ("tenant_id", 1)],
            [("flow_id", 1), ("tenant_id", 1)],
            [("contract_execution_id", 1), ("tenant_id", 1)],
            [("tenant_id", 1)],
        ]


class ContractExecutionDocument(Document):
    """Persistent representation of an openoma ContractExecution."""

    execution_id: UUID
    contract_id: UUID
    contract_version: int
    flow_execution_ids: list[UUID] = Field(default_factory=list)
    sub_contract_execution_ids: list[UUID] = Field(default_factory=list)
    assessment_executions: list[dict] = Field(default_factory=list)
    tenant_id: str

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "contract_executions"
        indexes = [
            [("execution_id", 1), ("tenant_id", 1)],
            [("contract_id", 1), ("tenant_id", 1)],
            [("tenant_id", 1)],
        ]
