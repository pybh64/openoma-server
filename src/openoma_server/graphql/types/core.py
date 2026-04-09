"""Strawberry GraphQL types for openoma core entities."""

from typing import Any

import strawberry


@strawberry.type
class PortDescriptorType:
    name: str
    description: str
    required: bool
    schema_def: strawberry.scalars.JSON | None = None
    metadata: strawberry.scalars.JSON | None = None


@strawberry.type
class PortMappingType:
    source_port: str
    target_port: str


@strawberry.type
class WorkBlockType:
    id: strawberry.ID
    version: int
    name: str
    description: str
    inputs: list[PortDescriptorType]
    outputs: list[PortDescriptorType]
    execution_hints: list[str]
    metadata: strawberry.scalars.JSON | None = None


@strawberry.type
class ConditionType:
    description: str
    predicate: strawberry.scalars.JSON | None = None
    metadata: strawberry.scalars.JSON | None = None


@strawberry.type
class NodeReferenceType:
    id: strawberry.ID
    target_id: strawberry.ID
    target_version: int
    alias: str | None = None
    metadata: strawberry.scalars.JSON | None = None


@strawberry.type
class EdgeType:
    source_id: strawberry.ID | None = None
    target_id: strawberry.ID
    condition: ConditionType | None = None
    port_mappings: list[PortMappingType] | None = None


@strawberry.type
class FlowType:
    id: strawberry.ID
    version: int
    name: str
    description: str
    nodes: list[NodeReferenceType]
    edges: list[EdgeType]
    expected_outcome: strawberry.scalars.JSON | None = None
    metadata: strawberry.scalars.JSON | None = None


@strawberry.type
class FlowReferenceType:
    flow_id: strawberry.ID
    flow_version: int
    alias: str | None = None
    metadata: strawberry.scalars.JSON | None = None


@strawberry.type
class ContractReferenceType:
    contract_id: strawberry.ID
    contract_version: int
    alias: str | None = None
    metadata: strawberry.scalars.JSON | None = None


@strawberry.type
class RequiredOutcomeType:
    id: strawberry.ID
    name: str
    description: str
    metadata: strawberry.scalars.JSON | None = None


@strawberry.type
class AssessmentBindingType:
    required_outcome_id: strawberry.ID
    assessment_flow_id: strawberry.ID
    assessment_flow_version: int
    test_flow_refs: list[FlowReferenceType]
    metadata: strawberry.scalars.JSON | None = None


@strawberry.type
class ContractType:
    id: strawberry.ID
    version: int
    name: str
    description: str
    work_flows: list[FlowReferenceType]
    sub_contracts: list[ContractReferenceType]
    required_outcomes: list[RequiredOutcomeType]
    assessment_bindings: list[AssessmentBindingType]
    metadata: strawberry.scalars.JSON | None = None


# --- Conversion helpers ---


def work_block_to_type(block: Any) -> WorkBlockType:
    return WorkBlockType(
        id=strawberry.ID(str(block.id)),
        version=block.version,
        name=block.name,
        description=block.description,
        inputs=[
            PortDescriptorType(
                name=p.name,
                description=p.description,
                required=p.required,
                schema_def=p.schema_ if hasattr(p, "schema_") else getattr(p, "schema", None),
                metadata=p.metadata or None,
            )
            for p in block.inputs
        ],
        outputs=[
            PortDescriptorType(
                name=p.name,
                description=p.description,
                required=p.required,
                schema_def=p.schema_ if hasattr(p, "schema_") else getattr(p, "schema", None),
                metadata=p.metadata or None,
            )
            for p in block.outputs
        ],
        execution_hints=list(block.execution_hints),
        metadata=block.metadata or None,
    )


def flow_to_type(flow: Any) -> FlowType:
    return FlowType(
        id=strawberry.ID(str(flow.id)),
        version=flow.version,
        name=flow.name,
        description=flow.description,
        nodes=[
            NodeReferenceType(
                id=strawberry.ID(str(n.id)),
                target_id=strawberry.ID(str(n.target_id)),
                target_version=n.target_version,
                alias=n.alias,
                metadata=n.metadata or None,
            )
            for n in flow.nodes
        ],
        edges=[
            EdgeType(
                source_id=strawberry.ID(str(e.source_id)) if e.source_id else None,
                target_id=strawberry.ID(str(e.target_id)),
                condition=ConditionType(
                    description=e.condition.description,
                    predicate=e.condition.predicate,
                    metadata=e.condition.metadata or None,
                )
                if e.condition
                else None,
                port_mappings=[
                    PortMappingType(source_port=pm.source_port, target_port=pm.target_port)
                    for pm in e.port_mappings
                ]
                if e.port_mappings
                else None,
            )
            for e in flow.edges
        ],
        expected_outcome=flow.expected_outcome,
        metadata=flow.metadata or None,
    )


def contract_to_type(contract: Any) -> ContractType:
    return ContractType(
        id=strawberry.ID(str(contract.id)),
        version=contract.version,
        name=contract.name,
        description=contract.description,
        work_flows=[
            FlowReferenceType(
                flow_id=strawberry.ID(str(wf.flow_id)),
                flow_version=wf.flow_version,
                alias=wf.alias,
                metadata=wf.metadata or None,
            )
            for wf in contract.work_flows
        ],
        sub_contracts=[
            ContractReferenceType(
                contract_id=strawberry.ID(str(sc.contract_id)),
                contract_version=sc.contract_version,
                alias=sc.alias,
                metadata=sc.metadata or None,
            )
            for sc in contract.sub_contracts
        ],
        required_outcomes=[
            RequiredOutcomeType(
                id=strawberry.ID(str(ro.id)),
                name=ro.name,
                description=ro.description,
                metadata=ro.metadata or None,
            )
            for ro in contract.required_outcomes
        ],
        assessment_bindings=[
            AssessmentBindingType(
                required_outcome_id=strawberry.ID(str(ab.required_outcome_id)),
                assessment_flow_id=strawberry.ID(str(ab.assessment_flow_id)),
                assessment_flow_version=ab.assessment_flow_version,
                test_flow_refs=[
                    FlowReferenceType(
                        flow_id=strawberry.ID(str(tr.flow_id)),
                        flow_version=tr.flow_version,
                        alias=tr.alias,
                        metadata=tr.metadata or None,
                    )
                    for tr in ab.test_flow_refs
                ],
                metadata=ab.metadata or None,
            )
            for ab in contract.assessment_bindings
        ],
        metadata=contract.metadata or None,
    )
