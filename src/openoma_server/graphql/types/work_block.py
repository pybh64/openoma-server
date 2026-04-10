from datetime import datetime
from uuid import UUID

import strawberry

from openoma_server.graphql.types.common import JSON


@strawberry.type
class PortDescriptorType:
    name: str
    description: str
    required: bool
    schema_def: JSON | None = strawberry.field(name="schema")
    metadata: JSON


@strawberry.type
class ExpectedOutcomeType:
    name: str
    description: str
    schema_def: JSON | None = strawberry.field(name="schema")
    metadata: JSON


@strawberry.type
class WorkBlockType:
    id: UUID
    version: int
    created_at: datetime
    created_by: str | None
    name: str
    description: str
    inputs: list[PortDescriptorType]
    outputs: list[PortDescriptorType]
    execution_hints: list[str]
    expected_outcome: ExpectedOutcomeType | None
    metadata: JSON
