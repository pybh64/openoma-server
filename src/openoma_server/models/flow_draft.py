"""FlowDraftDoc — mutable draft for flow editing before publish."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from beanie import Document
from pydantic import Field
from pymongo import IndexModel

from openoma_server.models.embedded import EdgeDoc, ExpectedOutcomeDoc, NodeReferenceDoc


class FlowDraftDoc(Document):
    draft_id: UUID = Field(default_factory=uuid4)
    base_flow_id: UUID | None = None
    base_flow_version: int | None = None
    name: str
    description: str = ""
    nodes: list[NodeReferenceDoc] = Field(default_factory=list)
    edges: list[EdgeDoc] = Field(default_factory=list)
    expected_outcome: ExpectedOutcomeDoc | None = None
    metadata: dict = Field(default_factory=dict)
    # Canvas layout embedded directly in draft
    node_positions: list[dict] = Field(default_factory=list)
    edge_layouts: list[dict] = Field(default_factory=list)
    viewport: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_by: str | None = None

    class Settings:
        name = "flow_drafts"
        indexes = [
            IndexModel([("draft_id", 1)], unique=True),
            IndexModel([("base_flow_id", 1), ("created_by", 1)]),
        ]

    @classmethod
    def new_id(cls) -> UUID:
        return uuid4()
