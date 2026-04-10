"""MongoDB implementation of the openoma ExecutionStore protocol."""

from __future__ import annotations

from uuid import UUID

from openoma.execution.block_execution import BlockExecution
from openoma.execution.contract_execution import ContractExecution
from openoma.execution.flow_execution import FlowExecution
from openoma.execution.types import ExecutionState
from openoma.store.execution_store import ExecutionOrderBy

from openoma_server.models.execution import (
    BlockExecutionDoc,
    ContractExecutionDoc,
    FlowExecutionDoc,
)


def _build_sort(
    order_by: ExecutionOrderBy | None, order_desc: bool
) -> list[tuple[str, int]]:
    if order_by is None:
        return [("created_at", -1)]
    direction = -1 if order_desc else 1
    return [(order_by, direction)]


class MongoExecutionStore:
    """MongoDB-backed ExecutionStore implementing the openoma protocol."""

    # ── BlockExecution ──────────────────────────────────────────────

    async def save_block_execution(self, execution: BlockExecution) -> None:
        existing = await BlockExecutionDoc.find_one(
            BlockExecutionDoc.execution_id == execution.id
        )
        if existing:
            existing.state = execution.state.value
            await existing.save()
        else:
            doc = BlockExecutionDoc.from_core(execution)
            await doc.insert()

    async def get_block_execution(self, id: UUID) -> BlockExecution | None:
        doc = await BlockExecutionDoc.find_one(
            BlockExecutionDoc.execution_id == id
        )
        return doc.to_core() if doc else None

    async def get_block_executions(self, ids: list[UUID]) -> list[BlockExecution]:
        docs = await BlockExecutionDoc.find(
            {"execution_id": {"$in": ids}}
        ).to_list()
        return [d.to_core() for d in docs]

    async def list_block_executions(
        self,
        work_block_id: UUID | None = None,
        *,
        flow_execution_id: UUID | None = None,
        state: ExecutionState | None = None,
        order_by: ExecutionOrderBy | None = None,
        order_desc: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[BlockExecution]:
        filters = []
        if work_block_id:
            filters.append(BlockExecutionDoc.work_block_id == work_block_id)
        if flow_execution_id:
            filters.append(BlockExecutionDoc.flow_execution_id == flow_execution_id)
        if state:
            filters.append(BlockExecutionDoc.state == state.value)

        sort_spec = _build_sort(order_by, order_desc)
        sort_str = [
            f"{'-' if d == -1 else '+'}{f}" for f, d in sort_spec
        ]

        docs = (
            await BlockExecutionDoc.find(*filters)
            .sort(*sort_str)
            .skip(offset)
            .limit(limit or 50)
            .to_list()
        )
        return [d.to_core() for d in docs]

    # ── FlowExecution ───────────────────────────────────────────────

    async def save_flow_execution(self, execution: FlowExecution) -> None:
        existing = await FlowExecutionDoc.find_one(
            FlowExecutionDoc.execution_id == execution.id
        )
        if existing:
            existing.state = execution.state.value
            existing.block_executions = list(execution.block_executions)
            await existing.save()
        else:
            doc = FlowExecutionDoc.from_core(execution)
            await doc.insert()

    async def get_flow_execution(self, id: UUID) -> FlowExecution | None:
        doc = await FlowExecutionDoc.find_one(
            FlowExecutionDoc.execution_id == id
        )
        return doc.to_core() if doc else None

    async def get_flow_executions(self, ids: list[UUID]) -> list[FlowExecution]:
        docs = await FlowExecutionDoc.find(
            {"execution_id": {"$in": ids}}
        ).to_list()
        return [d.to_core() for d in docs]

    async def list_flow_executions(
        self,
        flow_id: UUID | None = None,
        *,
        contract_execution_id: UUID | None = None,
        state: ExecutionState | None = None,
        order_by: ExecutionOrderBy | None = None,
        order_desc: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[FlowExecution]:
        filters = []
        if flow_id:
            filters.append(FlowExecutionDoc.flow_id == flow_id)
        if contract_execution_id:
            filters.append(FlowExecutionDoc.contract_execution_id == contract_execution_id)
        if state:
            filters.append(FlowExecutionDoc.state == state.value)

        sort_spec = _build_sort(order_by, order_desc)
        sort_str = [f"{'-' if d == -1 else '+'}{f}" for f, d in sort_spec]

        docs = (
            await FlowExecutionDoc.find(*filters)
            .sort(*sort_str)
            .skip(offset)
            .limit(limit or 50)
            .to_list()
        )
        return [d.to_core() for d in docs]

    # ── ContractExecution ───────────────────────────────────────────

    async def save_contract_execution(self, execution: ContractExecution) -> None:
        existing = await ContractExecutionDoc.find_one(
            ContractExecutionDoc.execution_id == execution.id
        )
        if existing:
            existing.state = execution.state.value
            existing.flow_executions = list(execution.flow_executions)
            existing.sub_contract_executions = list(execution.sub_contract_executions)
            await existing.save()
        else:
            doc = ContractExecutionDoc.from_core(execution)
            await doc.insert()

    async def get_contract_execution(self, id: UUID) -> ContractExecution | None:
        doc = await ContractExecutionDoc.find_one(
            ContractExecutionDoc.execution_id == id
        )
        return doc.to_core() if doc else None

    async def get_contract_executions(self, ids: list[UUID]) -> list[ContractExecution]:
        docs = await ContractExecutionDoc.find(
            {"execution_id": {"$in": ids}}
        ).to_list()
        return [d.to_core() for d in docs]

    async def list_contract_executions(
        self,
        contract_id: UUID | None = None,
        *,
        state: ExecutionState | None = None,
        order_by: ExecutionOrderBy | None = None,
        order_desc: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[ContractExecution]:
        filters = []
        if contract_id:
            filters.append(ContractExecutionDoc.contract_id == contract_id)
        if state:
            filters.append(ContractExecutionDoc.state == state.value)

        sort_spec = _build_sort(order_by, order_desc)
        sort_str = [f"{'-' if d == -1 else '+'}{f}" for f, d in sort_spec]

        docs = (
            await ContractExecutionDoc.find(*filters)
            .sort(*sort_str)
            .skip(offset)
            .limit(limit or 50)
            .to_list()
        )
        return [d.to_core() for d in docs]
