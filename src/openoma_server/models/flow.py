from datetime import UTC, datetime
from uuid import UUID, uuid4

from beanie import Document
from openoma.core.flow import Flow
from pymongo import IndexModel

from openoma_server.models.converters import (
    edge_from_doc,
    edge_to_doc,
    expected_outcome_from_doc,
    expected_outcome_to_doc,
    node_ref_from_doc,
    node_ref_to_doc,
)
from openoma_server.models.embedded import EdgeDoc, ExpectedOutcomeDoc, NodeReferenceDoc


class FlowDoc(Document):
    entity_id: UUID
    version: int = 1
    created_at: datetime = datetime.now(UTC)
    created_by: str | None = None
    name: str
    description: str = ""
    nodes: list[NodeReferenceDoc] = []
    edges: list[EdgeDoc] = []
    expected_outcome: ExpectedOutcomeDoc | None = None
    metadata: dict = {}

    class Settings:
        name = "flows"
        indexes = [
            IndexModel([("entity_id", 1), ("version", 1)], unique=True),
            IndexModel([("entity_id", 1), ("version", -1)]),
            IndexModel([("name", "text")]),
        ]

    def to_core(self) -> Flow:
        return Flow(
            id=self.entity_id,
            version=self.version,
            created_at=self.created_at,
            created_by=self.created_by,
            name=self.name,
            description=self.description,
            nodes=[node_ref_from_doc(n) for n in self.nodes],
            edges=[edge_from_doc(e) for e in self.edges],
            expected_outcome=(
                expected_outcome_from_doc(self.expected_outcome) if self.expected_outcome else None
            ),
            metadata=self.metadata,
        )

    @classmethod
    def from_core(cls, flow: Flow) -> "FlowDoc":
        return cls(
            entity_id=flow.id,
            version=flow.version,
            created_at=flow.created_at,
            created_by=flow.created_by,
            name=flow.name,
            description=flow.description,
            nodes=[node_ref_to_doc(n) for n in flow.nodes],
            edges=[edge_to_doc(e) for e in flow.edges],
            expected_outcome=(
                expected_outcome_to_doc(flow.expected_outcome) if flow.expected_outcome else None
            ),
            metadata=dict(flow.metadata),
        )

    @classmethod
    async def get_latest(cls, entity_id: UUID) -> "FlowDoc | None":
        return await cls.find_one(cls.entity_id == entity_id, sort=[("version", -1)])

    @classmethod
    async def get_by_version(cls, entity_id: UUID, version: int) -> "FlowDoc | None":
        return await cls.find_one(cls.entity_id == entity_id, cls.version == version)

    @classmethod
    async def get_next_version(cls, entity_id: UUID) -> int:
        latest = await cls.get_latest(entity_id)
        return (latest.version + 1) if latest else 1

    @classmethod
    async def list_latest(
        cls,
        name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list["FlowDoc"]:
        pipeline: list[dict] = []
        if name:
            pipeline.append({"$match": {"name": {"$regex": name, "$options": "i"}}})
        pipeline.extend(
            [
                {"$sort": {"entity_id": 1, "version": -1}},
                {"$group": {"_id": "$entity_id", "doc": {"$first": "$$ROOT"}}},
                {"$replaceRoot": {"newRoot": "$doc"}},
                {"$sort": {"created_at": -1}},
                {"$skip": offset},
                {"$limit": limit},
            ]
        )
        results = await cls.aggregate(pipeline).to_list()
        return [cls.model_validate(r) for r in results]

    @classmethod
    def new_id(cls) -> UUID:
        return uuid4()
