"""MongoDB implementation of the openoma DefinitionStore protocol.

Uses the Beanie document models for persistence and converts to/from
openoma core models at the boundary.
"""

from __future__ import annotations

from uuid import UUID

from openoma.core.contract import Contract, RequiredOutcome
from openoma.core.flow import Flow
from openoma.core.work_block import WorkBlock
from openoma.store.definition_store import DefinitionOrderBy, VersionRef

from openoma_server.models.contract import ContractDoc, RequiredOutcomeDoc
from openoma_server.models.flow import FlowDoc
from openoma_server.models.work_block import WorkBlockDoc


def _sort_key(order_by: DefinitionOrderBy | None, order_desc: bool) -> list[tuple[str, int]]:
    if order_by is None:
        return [("created_at", -1)]
    direction = -1 if order_desc else 1
    field_map = {"name": "name", "created_at": "created_at", "version": "version"}
    return [(field_map[order_by], direction)]


class MongoDefinitionStore:
    """MongoDB-backed DefinitionStore implementing the openoma protocol."""

    # ── WorkBlock ───────────────────────────────────────────────────

    async def save_work_block(self, block: WorkBlock) -> None:
        existing = await WorkBlockDoc.get_by_version(block.id, block.version)
        if existing:
            raise ValueError(f"WorkBlock ({block.id}, v{block.version}) already exists")
        doc = WorkBlockDoc.from_core(block)
        await doc.insert()

    async def get_work_block(self, id: UUID, version: int) -> WorkBlock | None:
        doc = await WorkBlockDoc.get_by_version(id, version)
        return doc.to_core() if doc else None

    async def get_work_blocks(self, refs: list[VersionRef]) -> list[WorkBlock]:
        results = []
        for entity_id, version in refs:
            doc = await WorkBlockDoc.get_by_version(entity_id, version)
            if doc:
                results.append(doc.to_core())
        return results

    async def get_latest_work_block(self, id: UUID) -> WorkBlock | None:
        doc = await WorkBlockDoc.get_latest(id)
        return doc.to_core() if doc else None

    async def list_work_blocks(
        self,
        *,
        name: str | None = None,
        order_by: DefinitionOrderBy | None = None,
        order_desc: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[WorkBlock]:
        docs = await WorkBlockDoc.list_latest(
            name=name, limit=limit or 50, offset=offset
        )
        return [d.to_core() for d in docs]

    # ── Flow ────────────────────────────────────────────────────────

    async def save_flow(self, flow: Flow) -> None:
        existing = await FlowDoc.get_by_version(flow.id, flow.version)
        if existing:
            raise ValueError(f"Flow ({flow.id}, v{flow.version}) already exists")
        doc = FlowDoc.from_core(flow)
        await doc.insert()

    async def get_flow(self, id: UUID, version: int) -> Flow | None:
        doc = await FlowDoc.get_by_version(id, version)
        return doc.to_core() if doc else None

    async def get_flows(self, refs: list[VersionRef]) -> list[Flow]:
        results = []
        for entity_id, version in refs:
            doc = await FlowDoc.get_by_version(entity_id, version)
            if doc:
                results.append(doc.to_core())
        return results

    async def get_latest_flow(self, id: UUID) -> Flow | None:
        doc = await FlowDoc.get_latest(id)
        return doc.to_core() if doc else None

    async def list_flows(
        self,
        *,
        name: str | None = None,
        order_by: DefinitionOrderBy | None = None,
        order_desc: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Flow]:
        docs = await FlowDoc.list_latest(name=name, limit=limit or 50, offset=offset)
        return [d.to_core() for d in docs]

    # ── Contract ────────────────────────────────────────────────────

    async def save_contract(self, contract: Contract) -> None:
        existing = await ContractDoc.get_by_version(contract.id, contract.version)
        if existing:
            raise ValueError(f"Contract ({contract.id}, v{contract.version}) already exists")
        doc = ContractDoc.from_core(contract)
        await doc.insert()

    async def get_contract(self, id: UUID, version: int) -> Contract | None:
        doc = await ContractDoc.get_by_version(id, version)
        return doc.to_core() if doc else None

    async def get_contracts(self, refs: list[VersionRef]) -> list[Contract]:
        results = []
        for entity_id, version in refs:
            doc = await ContractDoc.get_by_version(entity_id, version)
            if doc:
                results.append(doc.to_core())
        return results

    async def get_latest_contract(self, id: UUID) -> Contract | None:
        doc = await ContractDoc.get_latest(id)
        return doc.to_core() if doc else None

    async def list_contracts(
        self,
        *,
        name: str | None = None,
        order_by: DefinitionOrderBy | None = None,
        order_desc: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Contract]:
        docs = await ContractDoc.list_latest(name=name, limit=limit or 50, offset=offset)
        return [d.to_core() for d in docs]

    # ── RequiredOutcome ─────────────────────────────────────────────

    async def save_required_outcome(self, outcome: RequiredOutcome) -> None:
        existing = await RequiredOutcomeDoc.get_by_version(outcome.id, outcome.version)
        if existing:
            raise ValueError(
                f"RequiredOutcome ({outcome.id}, v{outcome.version}) already exists"
            )
        doc = RequiredOutcomeDoc.from_core(outcome)
        await doc.insert()

    async def get_required_outcome(self, id: UUID, version: int) -> RequiredOutcome | None:
        doc = await RequiredOutcomeDoc.get_by_version(id, version)
        return doc.to_core() if doc else None

    async def get_required_outcomes(self, refs: list[VersionRef]) -> list[RequiredOutcome]:
        results = []
        for entity_id, version in refs:
            doc = await RequiredOutcomeDoc.get_by_version(entity_id, version)
            if doc:
                results.append(doc.to_core())
        return results

    async def get_latest_required_outcome(self, id: UUID) -> RequiredOutcome | None:
        doc = await RequiredOutcomeDoc.get_latest(id)
        return doc.to_core() if doc else None

    async def list_required_outcomes(
        self,
        *,
        name: str | None = None,
        order_by: DefinitionOrderBy | None = None,
        order_desc: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[RequiredOutcome]:
        docs = await RequiredOutcomeDoc.list_latest(name=name, limit=limit or 50, offset=offset)
        return [d.to_core() for d in docs]
