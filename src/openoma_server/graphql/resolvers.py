"""Converter functions from Beanie docs to GraphQL types."""

from openoma_server.graphql.types.canvas_layout import (
    CanvasLayoutType,
    EdgeLayoutType,
    NodePositionType,
)
from openoma_server.graphql.types.contract import (
    AssessmentBindingType,
    ContractReferenceType,
    ContractType,
    FlowReferenceType,
    PartyType,
    RequiredOutcomeReferenceType,
    RequiredOutcomeType,
)
from openoma_server.graphql.types.execution import (
    AssessmentResultType,
    BlockExecutionType,
    ContractExecutionType,
    ExecutionEventType,
    ExecutionOutcomeType,
    ExecutorInfoType,
    FlowExecutionType,
)
from openoma_server.graphql.types.flow import (
    ConditionType,
    EdgeType,
    FlowType,
    NodeReferenceType,
    PortMappingType,
)
from openoma_server.graphql.types.flow_draft import FlowDraftType
from openoma_server.graphql.types.work_block import (
    ExpectedOutcomeType,
    PortDescriptorType,
    WorkBlockType,
)
from openoma_server.models.canvas_layout import (
    CanvasLayoutDoc,
    EdgeLayoutDoc,
    NodePositionDoc,
)
from openoma_server.models.contract import ContractDoc, RequiredOutcomeDoc
from openoma_server.models.embedded import (
    AssessmentBindingDoc,
    ConditionDoc,
    ContractReferenceDoc,
    EdgeDoc,
    ExpectedOutcomeDoc,
    FlowReferenceDoc,
    NodeReferenceDoc,
    PartyDoc,
    PortDescriptorDoc,
    PortMappingDoc,
    RequiredOutcomeReferenceDoc,
)
from openoma_server.models.execution import (
    BlockExecutionDoc,
    ContractExecutionDoc,
    ExecutionEventDoc,
    FlowExecutionDoc,
)
from openoma_server.models.flow import FlowDoc
from openoma_server.models.flow_draft import FlowDraftDoc
from openoma_server.models.work_block import WorkBlockDoc

# ── Canvas layout converters ──────────────────────────────────────


def _node_position(n: NodePositionDoc) -> NodePositionType:
    return NodePositionType(
        node_reference_id=n.node_reference_id,
        x=n.x,
        y=n.y,
        width=n.width,
        height=n.height,
        metadata=n.metadata,
    )


def _edge_layout(e: EdgeLayoutDoc) -> EdgeLayoutType:
    return EdgeLayoutType(
        source_id=e.source_id,
        target_id=e.target_id,
        bend_points=e.bend_points,
        label_position=e.label_position,
        metadata=e.metadata,
    )


def canvas_layout_to_gql(doc: CanvasLayoutDoc) -> CanvasLayoutType:
    return CanvasLayoutType(
        flow_id=doc.flow_id,
        flow_version=doc.flow_version,
        node_positions=[_node_position(n) for n in doc.node_positions],
        edge_layouts=[_edge_layout(e) for e in doc.edge_layouts],
        viewport=doc.viewport,
        updated_at=doc.updated_at,
        updated_by=doc.updated_by,
    )


def _port_desc(p: PortDescriptorDoc) -> PortDescriptorType:
    return PortDescriptorType(
        name=p.name,
        description=p.description,
        required=p.required,
        schema_def=p.schema_def,
        metadata=p.metadata,
    )


def _port_desc_from_core(p) -> PortDescriptorType:
    return PortDescriptorType(
        name=p.name,
        description=p.description,
        required=p.required,
        schema_def=p.schema_,
        metadata=dict(p.metadata),
    )


def _expected_outcome(e: ExpectedOutcomeDoc | None) -> ExpectedOutcomeType | None:
    if e is None:
        return None
    return ExpectedOutcomeType(
        name=e.name, description=e.description, schema_def=e.schema_def, metadata=e.metadata
    )


def _expected_outcome_from_core(e) -> ExpectedOutcomeType | None:
    if e is None:
        return None
    return ExpectedOutcomeType(
        name=e.name,
        description=e.description,
        schema_def=e.schema_,
        metadata=dict(e.metadata),
    )


def work_block_from_core(block) -> WorkBlockType:
    """Convert an openoma core WorkBlock to the GraphQL type."""
    return WorkBlockType(
        id=block.id,
        version=block.version,
        created_at=block.created_at,
        created_by=block.created_by,
        name=block.name,
        description=block.description,
        inputs=[_port_desc_from_core(p) for p in block.inputs],
        outputs=[_port_desc_from_core(p) for p in block.outputs],
        execution_hints=list(block.execution_hints),
        expected_outcome=_expected_outcome_from_core(block.expected_outcome),
        metadata=dict(block.metadata),
    )


def work_block_to_gql(doc: WorkBlockDoc) -> WorkBlockType:
    return WorkBlockType(
        id=doc.entity_id,
        version=doc.version,
        created_at=doc.created_at,
        created_by=doc.created_by,
        name=doc.name,
        description=doc.description,
        inputs=[_port_desc(p) for p in doc.inputs],
        outputs=[_port_desc(p) for p in doc.outputs],
        execution_hints=doc.execution_hints,
        expected_outcome=_expected_outcome(doc.expected_outcome),
        metadata=doc.metadata,
    )


def _condition(c: ConditionDoc | None) -> ConditionType | None:
    if c is None:
        return None
    return ConditionType(description=c.description, predicate=c.predicate, metadata=c.metadata)


def _port_mapping(pm: PortMappingDoc) -> PortMappingType:
    return PortMappingType(source_port=pm.source_port, target_port=pm.target_port)


def _node_ref(n: NodeReferenceDoc) -> NodeReferenceType:
    return NodeReferenceType(
        id=n.id,
        target_id=n.target_id,
        target_version=n.target_version,
        alias=n.alias,
        metadata=n.metadata,
    )


def _edge(e: EdgeDoc) -> EdgeType:
    return EdgeType(
        source_id=e.source_id,
        target_id=e.target_id,
        condition=_condition(e.condition),
        port_mappings=[_port_mapping(pm) for pm in e.port_mappings],
    )


def flow_to_gql(doc: FlowDoc) -> FlowType:
    return FlowType(
        id=doc.entity_id,
        version=doc.version,
        created_at=doc.created_at,
        created_by=doc.created_by,
        name=doc.name,
        description=doc.description,
        nodes=[_node_ref(n) for n in doc.nodes],
        edges=[_edge(e) for e in doc.edges],
        expected_outcome=_expected_outcome(doc.expected_outcome),
        metadata=doc.metadata,
    )


def flow_draft_to_gql(doc: FlowDraftDoc) -> FlowDraftType:
    return FlowDraftType(
        draft_id=doc.draft_id,
        base_flow_id=doc.base_flow_id,
        base_flow_version=doc.base_flow_version,
        name=doc.name,
        description=doc.description,
        nodes=[_node_ref(n) for n in doc.nodes],
        edges=[_edge(e) for e in doc.edges],
        expected_outcome=_expected_outcome(doc.expected_outcome),
        metadata=doc.metadata,
        node_positions=doc.node_positions,
        edge_layouts=doc.edge_layouts,
        viewport=doc.viewport,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        created_by=doc.created_by,
    )


def _flow_ref(r: FlowReferenceDoc) -> FlowReferenceType:
    return FlowReferenceType(
        flow_id=r.flow_id, flow_version=r.flow_version, alias=r.alias, metadata=r.metadata
    )


def _contract_ref(r: ContractReferenceDoc) -> ContractReferenceType:
    return ContractReferenceType(
        contract_id=r.contract_id,
        contract_version=r.contract_version,
        alias=r.alias,
        metadata=r.metadata,
    )


def _outcome_ref(r: RequiredOutcomeReferenceDoc) -> RequiredOutcomeReferenceType:
    return RequiredOutcomeReferenceType(
        required_outcome_id=r.required_outcome_id,
        required_outcome_version=r.required_outcome_version,
        alias=r.alias,
        metadata=r.metadata,
    )


def _party(p: PartyDoc) -> PartyType:
    return PartyType(name=p.name, role=p.role, contact=p.contact)


def _assessment_binding(b: AssessmentBindingDoc) -> AssessmentBindingType:
    return AssessmentBindingType(
        assessment_flow=_flow_ref(b.assessment_flow),
        test_flow_refs=[_flow_ref(r) for r in b.test_flow_refs],
        metadata=b.metadata,
    )


def required_outcome_to_gql(doc: RequiredOutcomeDoc) -> RequiredOutcomeType:
    return RequiredOutcomeType(
        id=doc.entity_id,
        version=doc.version,
        created_at=doc.created_at,
        created_by=doc.created_by,
        name=doc.name,
        description=doc.description,
        assessment_bindings=[_assessment_binding(b) for b in doc.assessment_bindings],
        metadata=doc.metadata,
    )


def contract_to_gql(doc: ContractDoc) -> ContractType:
    return ContractType(
        id=doc.entity_id,
        version=doc.version,
        created_at=doc.created_at,
        created_by=doc.created_by,
        name=doc.name,
        description=doc.description,
        owners=[_party(p) for p in doc.owners],
        work_flows=[_flow_ref(r) for r in doc.work_flows],
        sub_contracts=[_contract_ref(r) for r in doc.sub_contracts],
        required_outcomes=[_outcome_ref(r) for r in doc.required_outcomes],
        metadata=doc.metadata,
    )


# ── Execution converters ──────────────────────────────────────────


def execution_event_to_gql(doc: ExecutionEventDoc) -> ExecutionEventType:
    return ExecutionEventType(
        id=doc.event_id,
        timestamp=doc.timestamp,
        execution_id=doc.execution_id,
        event_type=doc.event_type,
        executor=(
            ExecutorInfoType(
                type=doc.executor.type,
                identifier=doc.executor.identifier,
                metadata=doc.executor.metadata,
            )
            if doc.executor
            else None
        ),
        outcome=(
            ExecutionOutcomeType(
                value=doc.outcome.value,
                metadata=doc.outcome.metadata,
            )
            if doc.outcome
            else None
        ),
        metadata=doc.metadata,
    )


def block_execution_to_gql(doc: BlockExecutionDoc) -> BlockExecutionType:
    return BlockExecutionType(
        id=doc.execution_id,
        flow_execution_id=doc.flow_execution_id,
        node_reference_id=doc.node_reference_id,
        work_block_id=doc.work_block_id,
        work_block_version=doc.work_block_version,
        state=doc.state,
        created_at=doc.created_at,
    )


def flow_execution_to_gql(doc: FlowExecutionDoc) -> FlowExecutionType:
    return FlowExecutionType(
        id=doc.execution_id,
        contract_execution_id=doc.contract_execution_id,
        flow_id=doc.flow_id,
        flow_version=doc.flow_version,
        _block_execution_ids=list(doc.block_executions),
        state=doc.state,
        created_at=doc.created_at,
    )


def _assessment_result_gql(doc) -> AssessmentResultType:
    return AssessmentResultType(
        required_outcome_id=doc.required_outcome_id,
        assessment_flow_execution_id=doc.assessment_flow_execution_id,
        result=doc.result,
    )


def contract_execution_to_gql(doc: ContractExecutionDoc) -> ContractExecutionType:
    return ContractExecutionType(
        id=doc.execution_id,
        contract_id=doc.contract_id,
        contract_version=doc.contract_version,
        _flow_execution_ids=list(doc.flow_executions),
        _sub_contract_execution_ids=list(doc.sub_contract_executions),
        assessment_executions=[_assessment_result_gql(a) for a in doc.assessment_executions],
        state=doc.state,
        created_at=doc.created_at,
    )
