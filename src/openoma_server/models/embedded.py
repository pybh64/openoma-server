"""Embedded Pydantic models shared across Beanie documents.

These mirror the openoma value objects but are not frozen so Beanie can
serialize them as embedded subdocuments.
"""

from uuid import UUID

from pydantic import BaseModel, Field


class PortDescriptorDoc(BaseModel):
    name: str
    description: str = ""
    required: bool = True
    schema_def: dict | None = Field(default=None, alias="schema")
    metadata: dict = Field(default_factory=dict)


class PortMappingDoc(BaseModel):
    source_port: str
    target_port: str


class ExpectedOutcomeDoc(BaseModel):
    name: str
    description: str = ""
    schema_def: dict | None = Field(default=None, alias="schema")
    metadata: dict = Field(default_factory=dict)


class ConditionDoc(BaseModel):
    description: str
    predicate: dict | None = None
    metadata: dict = Field(default_factory=dict)


class NodeReferenceDoc(BaseModel):
    id: UUID
    target_id: UUID
    target_version: int
    alias: str | None = None
    metadata: dict = Field(default_factory=dict)


class EdgeDoc(BaseModel):
    source_id: UUID | None = None
    target_id: UUID
    condition: ConditionDoc | None = None
    port_mappings: list[PortMappingDoc] = Field(default_factory=list)


class FlowReferenceDoc(BaseModel):
    flow_id: UUID
    flow_version: int
    alias: str | None = None
    metadata: dict = Field(default_factory=dict)


class ContractReferenceDoc(BaseModel):
    contract_id: UUID
    contract_version: int
    alias: str | None = None
    metadata: dict = Field(default_factory=dict)


class RequiredOutcomeReferenceDoc(BaseModel):
    required_outcome_id: UUID
    required_outcome_version: int
    alias: str | None = None
    metadata: dict = Field(default_factory=dict)


class PartyDoc(BaseModel):
    name: str
    role: str  # PartyRole value: "lead", "delegate", "approver", "reviewer"
    contact: str | None = None


class AssessmentBindingDoc(BaseModel):
    assessment_flow: FlowReferenceDoc
    test_flow_refs: list[FlowReferenceDoc] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class ExecutorInfoDoc(BaseModel):
    type: str  # "human", "agent", "system"
    identifier: str
    metadata: dict = Field(default_factory=dict)


class ExecutionOutcomeDoc(BaseModel):
    value: str | int | float | bool | dict | list | None = None
    metadata: dict = Field(default_factory=dict)


class AssessmentResultDoc(BaseModel):
    required_outcome_id: UUID
    assessment_flow_execution_id: UUID
    result: str | int | float | bool | dict | list | None = None
