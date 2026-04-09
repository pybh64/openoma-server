"""Beanie document models for openoma core entities."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from beanie import Document
from pydantic import Field


class WorkBlockDocument(Document):
    """Persistent representation of an openoma WorkBlock."""

    block_id: UUID
    version: int = 1
    name: str
    description: str = ""
    inputs: list[dict] = Field(default_factory=list)
    outputs: list[dict] = Field(default_factory=list)
    execution_hints: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    tenant_id: str

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "work_blocks"
        indexes = [
            [("block_id", 1), ("version", 1), ("tenant_id", 1)],
            [("tenant_id", 1)],
            [("name", 1), ("tenant_id", 1)],
        ]


class FlowDocument(Document):
    """Persistent representation of an openoma Flow."""

    flow_id: UUID
    version: int = 1
    name: str
    description: str = ""
    nodes: list[dict] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)
    expected_outcome: Any | None = None
    metadata: dict = Field(default_factory=dict)
    tenant_id: str

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "flows"
        indexes = [
            [("flow_id", 1), ("version", 1), ("tenant_id", 1)],
            [("tenant_id", 1)],
            [("name", 1), ("tenant_id", 1)],
        ]


class ContractDocument(Document):
    """Persistent representation of an openoma Contract."""

    contract_id: UUID
    version: int = 1
    name: str
    description: str = ""
    work_flows: list[dict] = Field(default_factory=list)
    sub_contracts: list[dict] = Field(default_factory=list)
    required_outcomes: list[dict] = Field(default_factory=list)
    assessment_bindings: list[dict] = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
    tenant_id: str

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "contracts"
        indexes = [
            [("contract_id", 1), ("version", 1), ("tenant_id", 1)],
            [("tenant_id", 1)],
            [("name", 1), ("tenant_id", 1)],
        ]
