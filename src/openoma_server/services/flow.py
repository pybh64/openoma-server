"""Flow service — business logic for creating and managing flows."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import strawberry
from openoma.core.condition import Condition
from openoma.core.flow import Edge, Flow, NodeReference
from openoma.core.types import ExpectedOutcome, PortMapping
from openoma.validation.graph import validate_flow

from openoma_server.auth.context import CurrentUser
from openoma_server.auth.permissions import check_object_permission
from openoma_server.graphql.inputs.flow import (
    CreateFlowInput,
    EdgeInput,
    NodeReferenceInput,
    UpdateFlowInput,
)
from openoma_server.graphql.inputs.work_block import ExpectedOutcomeInput
from openoma_server.models.flow import FlowDoc


def _convert_node_ref(n: NodeReferenceInput) -> NodeReference:
    return NodeReference(
        id=n.id or uuid4(),
        target_id=n.target_id,
        target_version=n.target_version,
        alias=n.alias,
        execution_schedule=n.execution_schedule,
        metadata=n.metadata or {},
    )


def _convert_edge(e: EdgeInput) -> Edge:
    return Edge(
        source_id=e.source_id,
        target_id=e.target_id,
        condition=(
            Condition(
                description=e.condition.description,
                predicate=e.condition.predicate,
                metadata=e.condition.metadata or {},
            )
            if e.condition
            else None
        ),
        port_mappings=[
            PortMapping(source_port=pm.source_port, target_port=pm.target_port)
            for pm in (e.port_mappings or [])
        ],
    )


def _convert_expected_outcome(e: ExpectedOutcomeInput) -> ExpectedOutcome:
    return ExpectedOutcome(
        name=e.name, description=e.description, schema=e.schema_def, metadata=e.metadata or {}
    )


async def create_flow(input: CreateFlowInput, user: CurrentUser) -> FlowDoc:
    entity_id = FlowDoc.new_id()

    flow = Flow(
        id=entity_id,
        version=1,
        created_at=datetime.now(UTC),
        created_by=user.display_name,
        name=input.name,
        description=input.description,
        nodes=[_convert_node_ref(n) for n in (input.nodes or [])],
        edges=[_convert_edge(e) for e in (input.edges or [])],
        expected_outcome=(
            _convert_expected_outcome(input.expected_outcome) if input.expected_outcome else None
        ),
        metadata=input.metadata or {},
    )

    validate_flow(flow)

    doc = FlowDoc.from_core(flow)
    check_object_permission(user, "create", doc)
    await doc.insert()
    return doc


async def update_flow(entity_id: UUID, input: UpdateFlowInput, user: CurrentUser) -> FlowDoc:
    latest = await FlowDoc.get_latest(entity_id)
    if latest is None:
        raise ValueError(f"Flow {entity_id} not found")

    check_object_permission(user, "update", latest)
    core = latest.to_core()
    new_version = await FlowDoc.get_next_version(entity_id)

    flow = Flow(
        id=core.id,
        version=new_version,
        created_at=datetime.now(UTC),
        created_by=user.display_name,
        name=input.name if input.name is not None else core.name,
        description=input.description if input.description is not None else core.description,
        nodes=(
            [_convert_node_ref(n) for n in input.nodes]
            if input.nodes is not None
            else list(core.nodes)
        ),
        edges=(
            [_convert_edge(e) for e in input.edges] if input.edges is not None else list(core.edges)
        ),
        expected_outcome=(
            _convert_expected_outcome(input.expected_outcome)
            if input.expected_outcome is not None and input.expected_outcome is not strawberry.UNSET
            else (core.expected_outcome if input.expected_outcome is strawberry.UNSET else None)
        ),
        metadata=input.metadata if input.metadata is not None else dict(core.metadata),
    )

    validate_flow(flow)

    doc = FlowDoc.from_core(flow)
    await doc.insert()
    return doc


async def get_flow(entity_id: UUID, version: int | None = None) -> FlowDoc | None:
    if version is not None:
        return await FlowDoc.get_by_version(entity_id, version)
    return await FlowDoc.get_latest(entity_id)


async def list_flows(name: str | None = None, limit: int = 50, offset: int = 0) -> list[FlowDoc]:
    return await FlowDoc.list_latest(name=name, limit=limit, offset=offset)
