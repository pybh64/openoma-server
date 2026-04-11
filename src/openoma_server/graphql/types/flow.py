from __future__ import annotations

from datetime import datetime
from uuid import UUID

import strawberry

from openoma_server.graphql.types.common import JSON
from openoma_server.graphql.types.work_block import ExpectedOutcomeType, WorkBlockType


@strawberry.type
class ConditionType:
    description: str
    predicate: JSON | None
    metadata: JSON


@strawberry.type
class PortMappingType:
    source_port: str
    target_port: str


@strawberry.type
class NodeReferenceType:
    id: UUID
    target_id: UUID
    target_version: int
    alias: str | None
    execution_schedule: str | None
    metadata: JSON

    @strawberry.field
    async def work_block(self, info: strawberry.Info) -> WorkBlockType | None:
        from openoma_server.graphql.resolvers import work_block_from_core

        core_block = await info.context.work_block_loader.load(
            (self.target_id, self.target_version)
        )
        return work_block_from_core(core_block) if core_block else None


@strawberry.type
class EdgeType:
    source_id: UUID | None
    target_id: UUID
    condition: ConditionType | None
    port_mappings: list[PortMappingType]


@strawberry.type
class FlowType:
    id: UUID
    version: int
    created_at: datetime
    created_by: str | None
    name: str
    description: str
    nodes: list[NodeReferenceType]
    edges: list[EdgeType]
    expected_outcome: ExpectedOutcomeType | None
    metadata: JSON
