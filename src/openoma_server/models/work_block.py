from datetime import UTC, datetime
from uuid import UUID, uuid4

from beanie import Document
from openoma.core.work_block import WorkBlock
from pymongo import IndexModel

from openoma_server.models.converters import (
    expected_outcome_from_doc,
    expected_outcome_to_doc,
    port_descriptor_from_doc,
    port_descriptor_to_doc,
)
from openoma_server.models.embedded import ExpectedOutcomeDoc, PortDescriptorDoc


class WorkBlockDoc(Document):
    entity_id: UUID
    version: int = 1
    created_at: datetime = datetime.now(UTC)
    created_by: str | None = None
    name: str
    description: str = ""
    inputs: list[PortDescriptorDoc] = []
    outputs: list[PortDescriptorDoc] = []
    execution_hints: list[str] = []
    expected_outcome: ExpectedOutcomeDoc | None = None
    metadata: dict = {}

    class Settings:
        name = "work_blocks"
        indexes = [
            IndexModel([("entity_id", 1), ("version", 1)], unique=True),
            IndexModel([("entity_id", 1), ("version", -1)]),
            IndexModel([("name", "text")]),
        ]

    def to_core(self) -> WorkBlock:
        return WorkBlock(
            id=self.entity_id,
            version=self.version,
            created_at=self.created_at,
            created_by=self.created_by,
            name=self.name,
            description=self.description,
            inputs=[port_descriptor_from_doc(p) for p in self.inputs],
            outputs=[port_descriptor_from_doc(p) for p in self.outputs],
            execution_hints=self.execution_hints,
            expected_outcome=(
                expected_outcome_from_doc(self.expected_outcome) if self.expected_outcome else None
            ),
            metadata=self.metadata,
        )

    @classmethod
    def from_core(cls, wb: WorkBlock) -> "WorkBlockDoc":
        return cls(
            entity_id=wb.id,
            version=wb.version,
            created_at=wb.created_at,
            created_by=wb.created_by,
            name=wb.name,
            description=wb.description,
            inputs=[port_descriptor_to_doc(p) for p in wb.inputs],
            outputs=[port_descriptor_to_doc(p) for p in wb.outputs],
            execution_hints=list(wb.execution_hints),
            expected_outcome=(
                expected_outcome_to_doc(wb.expected_outcome) if wb.expected_outcome else None
            ),
            metadata=dict(wb.metadata),
        )

    @classmethod
    async def get_latest(cls, entity_id: UUID) -> "WorkBlockDoc | None":
        return await cls.find_one(
            cls.entity_id == entity_id,
            sort=[("version", -1)],
        )

    @classmethod
    async def get_by_version(cls, entity_id: UUID, version: int) -> "WorkBlockDoc | None":
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
    ) -> list["WorkBlockDoc"]:
        """List the latest version of each work block, optionally filtered by name."""
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
