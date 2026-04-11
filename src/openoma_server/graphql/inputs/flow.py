from uuid import UUID

import strawberry

from openoma_server.graphql.inputs.work_block import ExpectedOutcomeInput
from openoma_server.graphql.types.common import JSON


@strawberry.input
class ConditionInput:
    description: str
    predicate: JSON | None = None
    metadata: JSON | None = None


@strawberry.input
class PortMappingInput:
    source_port: str
    target_port: str


@strawberry.input
class NodeReferenceInput:
    id: UUID | None = None  # Auto-generated if not provided
    target_id: UUID
    target_version: int
    alias: str | None = None
    execution_schedule: str | None = None
    metadata: JSON | None = None


@strawberry.input
class EdgeInput:
    source_id: UUID | None = None  # None for entry edges
    target_id: UUID
    condition: ConditionInput | None = None
    port_mappings: list[PortMappingInput] | None = None


@strawberry.input
class CreateFlowInput:
    name: str
    description: str = ""
    nodes: list[NodeReferenceInput] | None = None
    edges: list[EdgeInput] | None = None
    expected_outcome: ExpectedOutcomeInput | None = None
    metadata: JSON | None = None


@strawberry.input
class UpdateFlowInput:
    name: str | None = None
    description: str | None = None
    nodes: list[NodeReferenceInput] | None = None
    edges: list[EdgeInput] | None = None
    expected_outcome: ExpectedOutcomeInput | None = strawberry.UNSET
    metadata: JSON | None = None
