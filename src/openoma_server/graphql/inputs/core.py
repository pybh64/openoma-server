"""Strawberry input types for core entity mutations."""

from uuid import UUID

import strawberry


@strawberry.input
class PortDescriptorInput:
    name: str
    description: str = ""
    required: bool = True
    schema_def: strawberry.scalars.JSON | None = None
    metadata: strawberry.scalars.JSON | None = None


@strawberry.input
class CreateWorkBlockInput:
    name: str
    description: str = ""
    inputs: list[PortDescriptorInput] | None = None
    outputs: list[PortDescriptorInput] | None = None
    execution_hints: list[str] | None = None
    metadata: strawberry.scalars.JSON | None = None


@strawberry.input
class UpdateWorkBlockInput:
    id: UUID
    name: str | None = None
    description: str | None = None
    inputs: list[PortDescriptorInput] | None = None
    outputs: list[PortDescriptorInput] | None = None
    execution_hints: list[str] | None = None
    metadata: strawberry.scalars.JSON | None = None


@strawberry.input
class PortMappingInput:
    source_port: str
    target_port: str


@strawberry.input
class ConditionInput:
    description: str
    predicate: strawberry.scalars.JSON | None = None
    metadata: strawberry.scalars.JSON | None = None


@strawberry.input
class NodeReferenceInput:
    id: UUID | None = None
    target_id: UUID
    target_version: int
    alias: str | None = None
    metadata: strawberry.scalars.JSON | None = None


@strawberry.input
class EdgeInput:
    source_id: UUID | None = None
    target_id: UUID
    condition: ConditionInput | None = None
    port_mappings: list[PortMappingInput] | None = None


@strawberry.input
class CreateFlowInput:
    name: str
    description: str = ""
    nodes: list[NodeReferenceInput] | None = None
    edges: list[EdgeInput] | None = None
    expected_outcome: strawberry.scalars.JSON | None = None
    metadata: strawberry.scalars.JSON | None = None
    is_assessment: bool = False


@strawberry.input
class UpdateFlowInput:
    id: UUID
    name: str | None = None
    description: str | None = None
    nodes: list[NodeReferenceInput] | None = None
    edges: list[EdgeInput] | None = None
    expected_outcome: strawberry.scalars.JSON | None = None
    metadata: strawberry.scalars.JSON | None = None
    is_assessment: bool = False


@strawberry.input
class FlowReferenceInput:
    flow_id: UUID
    flow_version: int
    alias: str | None = None
    metadata: strawberry.scalars.JSON | None = None


@strawberry.input
class ContractReferenceInput:
    contract_id: UUID
    contract_version: int
    alias: str | None = None
    metadata: strawberry.scalars.JSON | None = None


@strawberry.input
class RequiredOutcomeInput:
    id: UUID | None = None
    name: str
    description: str = ""
    metadata: strawberry.scalars.JSON | None = None


@strawberry.input
class AssessmentBindingInput:
    required_outcome_id: UUID
    assessment_flow_id: UUID
    assessment_flow_version: int
    test_flow_refs: list[FlowReferenceInput] | None = None
    metadata: strawberry.scalars.JSON | None = None


@strawberry.input
class CreateContractInput:
    name: str
    description: str = ""
    work_flows: list[FlowReferenceInput] | None = None
    sub_contracts: list[ContractReferenceInput] | None = None
    required_outcomes: list[RequiredOutcomeInput] | None = None
    assessment_bindings: list[AssessmentBindingInput] | None = None
    metadata: strawberry.scalars.JSON | None = None


@strawberry.input
class UpdateContractInput:
    id: UUID
    name: str | None = None
    description: str | None = None
    work_flows: list[FlowReferenceInput] | None = None
    sub_contracts: list[ContractReferenceInput] | None = None
    required_outcomes: list[RequiredOutcomeInput] | None = None
    assessment_bindings: list[AssessmentBindingInput] | None = None
    metadata: strawberry.scalars.JSON | None = None
