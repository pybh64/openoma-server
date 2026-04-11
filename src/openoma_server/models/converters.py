"""Conversion utilities between Beanie embedded docs and openoma core models."""

from openoma.core.condition import Condition
from openoma.core.contract import AssessmentBinding
from openoma.core.flow import Edge, NodeReference
from openoma.core.types import (
    ContractReference,
    ExpectedOutcome,
    FlowReference,
    Party,
    PartyRole,
    PortDescriptor,
    PortMapping,
    RequiredOutcomeReference,
)
from openoma.execution.types import AssessmentResult, ExecutionOutcome, ExecutorInfo

from openoma_server.models.embedded import (
    AssessmentBindingDoc,
    AssessmentResultDoc,
    ConditionDoc,
    ContractReferenceDoc,
    EdgeDoc,
    ExecutionOutcomeDoc,
    ExecutorInfoDoc,
    ExpectedOutcomeDoc,
    FlowReferenceDoc,
    NodeReferenceDoc,
    PartyDoc,
    PortDescriptorDoc,
    PortMappingDoc,
    RequiredOutcomeReferenceDoc,
)

# --- PortDescriptor ---


def port_descriptor_to_doc(p: PortDescriptor) -> PortDescriptorDoc:
    return PortDescriptorDoc(
        name=p.name,
        description=p.description,
        required=p.required,
        schema=p.schema_,
        metadata=p.metadata,
    )


def port_descriptor_from_doc(d: PortDescriptorDoc) -> PortDescriptor:
    return PortDescriptor(
        name=d.name,
        description=d.description,
        required=d.required,
        schema=d.schema_def,
        metadata=d.metadata,
    )


# --- PortMapping ---


def port_mapping_to_doc(p: PortMapping) -> PortMappingDoc:
    return PortMappingDoc(source_port=p.source_port, target_port=p.target_port)


def port_mapping_from_doc(d: PortMappingDoc) -> PortMapping:
    return PortMapping(source_port=d.source_port, target_port=d.target_port)


# --- ExpectedOutcome ---


def expected_outcome_to_doc(e: ExpectedOutcome) -> ExpectedOutcomeDoc:
    return ExpectedOutcomeDoc(
        name=e.name, description=e.description, schema=e.schema_, metadata=e.metadata
    )


def expected_outcome_from_doc(d: ExpectedOutcomeDoc) -> ExpectedOutcome:
    return ExpectedOutcome(
        name=d.name, description=d.description, schema=d.schema_def, metadata=d.metadata
    )


# --- Condition ---


def condition_to_doc(c: Condition) -> ConditionDoc:
    return ConditionDoc(description=c.description, predicate=c.predicate, metadata=c.metadata)


def condition_from_doc(d: ConditionDoc) -> Condition:
    return Condition(description=d.description, predicate=d.predicate, metadata=d.metadata)


# --- NodeReference ---


def node_ref_to_doc(n: NodeReference) -> NodeReferenceDoc:
    return NodeReferenceDoc(
        id=n.id,
        target_id=n.target_id,
        target_version=n.target_version,
        alias=n.alias,
        execution_schedule=n.execution_schedule,
        metadata=n.metadata,
    )


def node_ref_from_doc(d: NodeReferenceDoc) -> NodeReference:
    return NodeReference(
        id=d.id,
        target_id=d.target_id,
        target_version=d.target_version,
        alias=d.alias,
        execution_schedule=d.execution_schedule,
        metadata=d.metadata,
    )


# --- Edge ---


def edge_to_doc(e: Edge) -> EdgeDoc:
    return EdgeDoc(
        source_id=e.source_id,
        target_id=e.target_id,
        condition=condition_to_doc(e.condition) if e.condition else None,
        port_mappings=[port_mapping_to_doc(pm) for pm in e.port_mappings],
    )


def edge_from_doc(d: EdgeDoc) -> Edge:
    return Edge(
        source_id=d.source_id,
        target_id=d.target_id,
        condition=condition_from_doc(d.condition) if d.condition else None,
        port_mappings=[port_mapping_from_doc(pm) for pm in d.port_mappings],
    )


# --- FlowReference ---


def flow_ref_to_doc(r: FlowReference) -> FlowReferenceDoc:
    return FlowReferenceDoc(
        flow_id=r.flow_id, flow_version=r.flow_version, alias=r.alias, metadata=r.metadata
    )


def flow_ref_from_doc(d: FlowReferenceDoc) -> FlowReference:
    return FlowReference(
        flow_id=d.flow_id, flow_version=d.flow_version, alias=d.alias, metadata=d.metadata
    )


# --- ContractReference ---


def contract_ref_to_doc(r: ContractReference) -> ContractReferenceDoc:
    return ContractReferenceDoc(
        contract_id=r.contract_id,
        contract_version=r.contract_version,
        alias=r.alias,
        metadata=r.metadata,
    )


def contract_ref_from_doc(d: ContractReferenceDoc) -> ContractReference:
    return ContractReference(
        contract_id=d.contract_id,
        contract_version=d.contract_version,
        alias=d.alias,
        metadata=d.metadata,
    )


# --- RequiredOutcomeReference ---


def outcome_ref_to_doc(r: RequiredOutcomeReference) -> RequiredOutcomeReferenceDoc:
    return RequiredOutcomeReferenceDoc(
        required_outcome_id=r.required_outcome_id,
        required_outcome_version=r.required_outcome_version,
        alias=r.alias,
        metadata=r.metadata,
    )


def outcome_ref_from_doc(d: RequiredOutcomeReferenceDoc) -> RequiredOutcomeReference:
    return RequiredOutcomeReference(
        required_outcome_id=d.required_outcome_id,
        required_outcome_version=d.required_outcome_version,
        alias=d.alias,
        metadata=d.metadata,
    )


# --- Party ---


def party_to_doc(p: Party) -> PartyDoc:
    return PartyDoc(name=p.name, role=p.role.value, contact=p.contact)


def party_from_doc(d: PartyDoc) -> Party:
    return Party(name=d.name, role=PartyRole(d.role), contact=d.contact)


# --- AssessmentBinding ---


def assessment_binding_to_doc(b: AssessmentBinding) -> AssessmentBindingDoc:
    return AssessmentBindingDoc(
        assessment_flow=flow_ref_to_doc(b.assessment_flow),
        test_flow_refs=[flow_ref_to_doc(r) for r in b.test_flow_refs],
        metadata=b.metadata,
    )


def assessment_binding_from_doc(d: AssessmentBindingDoc) -> AssessmentBinding:
    return AssessmentBinding(
        assessment_flow=flow_ref_from_doc(d.assessment_flow),
        test_flow_refs=[flow_ref_from_doc(r) for r in d.test_flow_refs],
        metadata=d.metadata,
    )


# --- ExecutorInfo ---


def executor_info_to_doc(e: ExecutorInfo) -> ExecutorInfoDoc:
    return ExecutorInfoDoc(type=e.type, identifier=e.identifier, metadata=e.metadata)


def executor_info_from_doc(d: ExecutorInfoDoc) -> ExecutorInfo:
    return ExecutorInfo(type=d.type, identifier=d.identifier, metadata=d.metadata)


# --- ExecutionOutcome ---


def execution_outcome_to_doc(o: ExecutionOutcome) -> ExecutionOutcomeDoc:
    return ExecutionOutcomeDoc(value=o.value, metadata=o.metadata)


def execution_outcome_from_doc(d: ExecutionOutcomeDoc) -> ExecutionOutcome:
    return ExecutionOutcome(value=d.value, metadata=d.metadata)


# --- AssessmentResult ---


def assessment_result_to_doc(r: AssessmentResult) -> AssessmentResultDoc:
    return AssessmentResultDoc(
        required_outcome_id=r.required_outcome_id,
        assessment_flow_execution_id=r.assessment_flow_execution_id,
        result=r.result,
    )


def assessment_result_from_doc(d: AssessmentResultDoc) -> AssessmentResult:
    return AssessmentResult(
        required_outcome_id=d.required_outcome_id,
        assessment_flow_execution_id=d.assessment_flow_execution_id,
        result=d.result,
    )
