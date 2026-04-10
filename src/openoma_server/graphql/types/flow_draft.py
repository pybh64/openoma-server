"""GraphQL types for flow drafts."""

from datetime import datetime
from uuid import UUID

import strawberry

from openoma_server.graphql.types.common import JSON
from openoma_server.graphql.types.flow import EdgeType, NodeReferenceType
from openoma_server.graphql.types.work_block import ExpectedOutcomeType


@strawberry.type
class FlowDraftType:
    draft_id: UUID
    base_flow_id: UUID | None
    base_flow_version: int | None
    name: str
    description: str
    nodes: list[NodeReferenceType]
    edges: list[EdgeType]
    expected_outcome: ExpectedOutcomeType | None
    metadata: JSON
    node_positions: list[JSON]
    edge_layouts: list[JSON]
    viewport: JSON
    created_at: datetime
    updated_at: datetime
    created_by: str | None
