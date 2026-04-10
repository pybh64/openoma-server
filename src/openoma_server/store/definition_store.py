"""MongoDB implementation of the openoma DefinitionStore protocol.

Uses the Beanie document models for persistence and converts to/from
openoma core models at the boundary.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
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


def _build_definition_filter(filter_dict: dict[str, Any] | None) -> dict[str, Any]:
    """Convert a filter dict with known keys into a MongoDB $match condition."""
    if not filter_dict:
        return {}
    match: dict[str, Any] = {}
    if filter_dict.get("name"):
        match["name"] = {"$regex": filter_dict["name"], "$options": "i"}
    if filter_dict.get("created_by"):
        match["created_by"] = filter_dict["created_by"]
    if filter_dict.get("created_after"):
        match.setdefault("created_at", {})["$gte"] = filter_dict["created_after"]
    if filter_dict.get("created_before"):
        match.setdefault("created_at", {})["$lte"] = filter_dict["created_before"]
    return match


def _latest_version_pipeline() -> list[dict]:
    """Pipeline stages to keep only the latest version per entity_id."""
    return [
        {"$sort": {"entity_id": 1, "version": -1}},
        {"$group": {"_id": "$entity_id", "doc": {"$first": "$$ROOT"}}},
        {"$replaceRoot": {"newRoot": "$doc"}},
    ]


async def _run_definition_connection(
    doc_cls: type,
    *,
    first: int = 50,
    after_cursor: tuple[str, str] | None = None,
    filter_dict: dict[str, Any] | None = None,
    sort_field: str = "created_at",
    sort_direction: int = -1,
) -> tuple[list, int, bool]:
    """Generic connection query for versioned definition documents.

    Returns (docs, total_count, has_next_page).
    """
    match_stage = _build_definition_filter(filter_dict)

    # ── count pipeline (total matching, no cursor / limit) ────────
    count_pipeline: list[dict] = [*_latest_version_pipeline()]
    if match_stage:
        count_pipeline.append({"$match": match_stage})
    count_pipeline.append({"$count": "total"})
    count_result = await doc_cls.aggregate(count_pipeline).to_list()
    total_count = count_result[0]["total"] if count_result else 0

    # ── data pipeline ─────────────────────────────────────────────
    pipeline: list[dict] = [*_latest_version_pipeline()]
    if match_stage:
        pipeline.append({"$match": match_stage})

    # Sort (with entity_id tiebreaker for stable ordering)
    pipeline.append({"$sort": {sort_field: sort_direction, "entity_id": 1}})

    # Keyset cursor condition
    if after_cursor:
        cursor_sort_val, cursor_eid = after_cursor
        # Parse cursor_sort_val back to datetime if sorting by a date field
        if sort_field == "created_at":
            cursor_sort_val = datetime.fromisoformat(cursor_sort_val)
        if sort_direction == -1:
            # DESC: next page has values *less than* cursor, or equal with entity_id > cursor
            pipeline.append(
                {
                    "$match": {
                        "$or": [
                            {sort_field: {"$lt": cursor_sort_val}},
                            {sort_field: cursor_sort_val, "entity_id": {"$gt": cursor_eid}},
                        ]
                    }
                }
            )
        else:
            # ASC: next page has values *greater than* cursor, or equal with entity_id > cursor
            pipeline.append(
                {
                    "$match": {
                        "$or": [
                            {sort_field: {"$gt": cursor_sort_val}},
                            {sort_field: cursor_sort_val, "entity_id": {"$gt": cursor_eid}},
                        ]
                    }
                }
            )

    # Fetch one extra to detect has_next_page
    pipeline.append({"$limit": first + 1})

    results = await doc_cls.aggregate(pipeline).to_list()
    docs = [doc_cls.model_validate(r) for r in results]

    has_next = len(docs) > first
    if has_next:
        docs = docs[:first]

    return docs, total_count, has_next


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
        if not refs:
            return []
        or_clauses = [{"entity_id": eid, "version": ver} for eid, ver in refs]
        docs = await WorkBlockDoc.find({"$or": or_clauses}).to_list()
        return [d.to_core() for d in docs]

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

    async def list_work_blocks_connection(
        self,
        *,
        first: int = 50,
        after: tuple[str, str] | None = None,
        filter: dict | None = None,
        sort_field: str = "created_at",
        sort_direction: int = -1,
    ) -> tuple[list[WorkBlockDoc], int, bool]:
        """Cursor-paginated list of latest work blocks.

        Returns (docs, total_count, has_next_page).
        """
        return await _run_definition_connection(
            WorkBlockDoc,
            first=first,
            after_cursor=after,
            filter_dict=filter,
            sort_field=sort_field,
            sort_direction=sort_direction,
        )

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
        if not refs:
            return []
        or_clauses = [{"entity_id": eid, "version": ver} for eid, ver in refs]
        docs = await FlowDoc.find({"$or": or_clauses}).to_list()
        return [d.to_core() for d in docs]

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

    async def list_flows_connection(
        self,
        *,
        first: int = 50,
        after: tuple[str, str] | None = None,
        filter: dict | None = None,
        sort_field: str = "created_at",
        sort_direction: int = -1,
    ) -> tuple[list[FlowDoc], int, bool]:
        """Cursor-paginated list of latest flows.

        Returns (docs, total_count, has_next_page).
        """
        return await _run_definition_connection(
            FlowDoc,
            first=first,
            after_cursor=after,
            filter_dict=filter,
            sort_field=sort_field,
            sort_direction=sort_direction,
        )

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
        if not refs:
            return []
        or_clauses = [{"entity_id": eid, "version": ver} for eid, ver in refs]
        docs = await ContractDoc.find({"$or": or_clauses}).to_list()
        return [d.to_core() for d in docs]

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

    async def list_contracts_connection(
        self,
        *,
        first: int = 50,
        after: tuple[str, str] | None = None,
        filter: dict | None = None,
        sort_field: str = "created_at",
        sort_direction: int = -1,
    ) -> tuple[list[ContractDoc], int, bool]:
        """Cursor-paginated list of latest contracts.

        Returns (docs, total_count, has_next_page).
        """
        return await _run_definition_connection(
            ContractDoc,
            first=first,
            after_cursor=after,
            filter_dict=filter,
            sort_field=sort_field,
            sort_direction=sort_direction,
        )

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
        if not refs:
            return []
        or_clauses = [{"entity_id": eid, "version": ver} for eid, ver in refs]
        docs = await RequiredOutcomeDoc.find({"$or": or_clauses}).to_list()
        return [d.to_core() for d in docs]

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
