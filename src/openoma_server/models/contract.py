from datetime import UTC, datetime
from uuid import UUID, uuid4

from beanie import Document
from openoma.core.contract import Contract, RequiredOutcome
from pymongo import IndexModel

from openoma_server.models.converters import (
    assessment_binding_from_doc,
    assessment_binding_to_doc,
    contract_ref_from_doc,
    contract_ref_to_doc,
    flow_ref_from_doc,
    flow_ref_to_doc,
    outcome_ref_from_doc,
    outcome_ref_to_doc,
    party_from_doc,
    party_to_doc,
)
from openoma_server.models.embedded import (
    AssessmentBindingDoc,
    ContractReferenceDoc,
    FlowReferenceDoc,
    PartyDoc,
    RequiredOutcomeReferenceDoc,
)


class RequiredOutcomeDoc(Document):
    entity_id: UUID
    version: int = 1
    created_at: datetime = datetime.now(UTC)
    created_by: str | None = None
    name: str
    description: str = ""
    assessment_bindings: list[AssessmentBindingDoc] = []
    metadata: dict = {}

    class Settings:
        name = "required_outcomes"
        indexes = [
            IndexModel([("entity_id", 1), ("version", 1)], unique=True),
            IndexModel([("entity_id", 1), ("version", -1)]),
            IndexModel([("name", "text")]),
        ]

    def to_core(self) -> RequiredOutcome:
        return RequiredOutcome(
            id=self.entity_id,
            version=self.version,
            created_at=self.created_at,
            created_by=self.created_by,
            name=self.name,
            description=self.description,
            assessment_bindings=[assessment_binding_from_doc(b) for b in self.assessment_bindings],
            metadata=self.metadata,
        )

    @classmethod
    def from_core(cls, ro: RequiredOutcome) -> "RequiredOutcomeDoc":
        return cls(
            entity_id=ro.id,
            version=ro.version,
            created_at=ro.created_at,
            created_by=ro.created_by,
            name=ro.name,
            description=ro.description,
            assessment_bindings=[assessment_binding_to_doc(b) for b in ro.assessment_bindings],
            metadata=dict(ro.metadata),
        )

    @classmethod
    async def get_latest(cls, entity_id: UUID) -> "RequiredOutcomeDoc | None":
        return await cls.find_one(cls.entity_id == entity_id, sort=[("version", -1)])

    @classmethod
    async def get_by_version(cls, entity_id: UUID, version: int) -> "RequiredOutcomeDoc | None":
        return await cls.find_one(cls.entity_id == entity_id, cls.version == version)

    @classmethod
    async def get_next_version(cls, entity_id: UUID) -> int:
        latest = await cls.get_latest(entity_id)
        return (latest.version + 1) if latest else 1

    @classmethod
    async def list_latest(
        cls, name: str | None = None, limit: int = 50, offset: int = 0
    ) -> list["RequiredOutcomeDoc"]:
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


class ContractDoc(Document):
    entity_id: UUID
    version: int = 1
    created_at: datetime = datetime.now(UTC)
    created_by: str | None = None
    name: str
    description: str = ""
    owners: list[PartyDoc] = []
    work_flows: list[FlowReferenceDoc] = []
    sub_contracts: list[ContractReferenceDoc] = []
    required_outcomes: list[RequiredOutcomeReferenceDoc] = []
    metadata: dict = {}

    class Settings:
        name = "contracts"
        indexes = [
            IndexModel([("entity_id", 1), ("version", 1)], unique=True),
            IndexModel([("entity_id", 1), ("version", -1)]),
            IndexModel([("name", "text")]),
        ]

    def to_core(self) -> Contract:
        return Contract(
            id=self.entity_id,
            version=self.version,
            created_at=self.created_at,
            created_by=self.created_by,
            name=self.name,
            description=self.description,
            owners=[party_from_doc(p) for p in self.owners],
            work_flows=[flow_ref_from_doc(r) for r in self.work_flows],
            sub_contracts=[contract_ref_from_doc(r) for r in self.sub_contracts],
            required_outcomes=[outcome_ref_from_doc(r) for r in self.required_outcomes],
            metadata=self.metadata,
        )

    @classmethod
    def from_core(cls, c: Contract) -> "ContractDoc":
        return cls(
            entity_id=c.id,
            version=c.version,
            created_at=c.created_at,
            created_by=c.created_by,
            name=c.name,
            description=c.description,
            owners=[party_to_doc(p) for p in c.owners],
            work_flows=[flow_ref_to_doc(r) for r in c.work_flows],
            sub_contracts=[contract_ref_to_doc(r) for r in c.sub_contracts],
            required_outcomes=[outcome_ref_to_doc(r) for r in c.required_outcomes],
            metadata=dict(c.metadata),
        )

    @classmethod
    async def get_latest(cls, entity_id: UUID) -> "ContractDoc | None":
        return await cls.find_one(cls.entity_id == entity_id, sort=[("version", -1)])

    @classmethod
    async def get_by_version(cls, entity_id: UUID, version: int) -> "ContractDoc | None":
        return await cls.find_one(cls.entity_id == entity_id, cls.version == version)

    @classmethod
    async def get_next_version(cls, entity_id: UUID) -> int:
        latest = await cls.get_latest(entity_id)
        return (latest.version + 1) if latest else 1

    @classmethod
    async def list_latest(
        cls, name: str | None = None, limit: int = 50, offset: int = 0
    ) -> list["ContractDoc"]:
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
