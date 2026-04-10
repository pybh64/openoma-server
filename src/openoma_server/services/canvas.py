"""Service functions for composite canvas data retrieval."""

from __future__ import annotations

from uuid import UUID

from openoma_server.models.canvas_layout import CanvasLayoutDoc
from openoma_server.models.execution import (
    BlockExecutionDoc,
    ExecutionEventDoc,
    FlowExecutionDoc,
)
from openoma_server.models.flow import FlowDoc
from openoma_server.models.work_block import WorkBlockDoc


async def get_flow_canvas_data(
    flow_id: UUID, flow_version: int | None = None
) -> tuple[FlowDoc, CanvasLayoutDoc | None, list[WorkBlockDoc]] | None:
    """Get flow + layout + work block docs for canvas rendering.

    If flow_version is None, fetches the latest version.
    Returns None if the flow is not found.
    """
    if flow_version is not None:
        flow_doc = await FlowDoc.get_by_version(flow_id, flow_version)
    else:
        flow_doc = await FlowDoc.get_latest(flow_id)

    if not flow_doc:
        return None

    layout_doc = await CanvasLayoutDoc.find_one(
        CanvasLayoutDoc.flow_id == flow_id,
        CanvasLayoutDoc.flow_version == flow_doc.version,
    )

    refs = [(n.target_id, n.target_version) for n in flow_doc.nodes]
    if refs:
        or_clauses = [{"entity_id": eid, "version": ver} for eid, ver in refs]
        wb_docs = await WorkBlockDoc.find({"$or": or_clauses}).to_list()
    else:
        wb_docs = []

    return flow_doc, layout_doc, wb_docs


async def get_flow_execution_canvas_data(
    flow_execution_id: UUID,
) -> (
    tuple[
        FlowDoc,
        CanvasLayoutDoc | None,
        FlowExecutionDoc,
        list[BlockExecutionDoc],
        dict[UUID, ExecutionEventDoc],
    ]
    | None
):
    """Get flow execution + flow + layout + per-node execution states.

    Returns None if the flow execution is not found.
    """
    flow_exec_doc = await FlowExecutionDoc.find_one(
        FlowExecutionDoc.execution_id == flow_execution_id
    )
    if not flow_exec_doc:
        return None

    flow_doc = await FlowDoc.get_by_version(
        flow_exec_doc.flow_id, flow_exec_doc.flow_version
    )
    if not flow_doc:
        return None

    layout_doc = await CanvasLayoutDoc.find_one(
        CanvasLayoutDoc.flow_id == flow_exec_doc.flow_id,
        CanvasLayoutDoc.flow_version == flow_exec_doc.flow_version,
    )

    block_exec_docs = await BlockExecutionDoc.find(
        BlockExecutionDoc.flow_execution_id == flow_execution_id
    ).to_list()

    exec_ids = [be.execution_id for be in block_exec_docs]
    latest_by_exec: dict[UUID, ExecutionEventDoc] = {}
    if exec_ids:
        event_docs = (
            await ExecutionEventDoc.find({"execution_id": {"$in": exec_ids}})
            .sort(-ExecutionEventDoc.timestamp)
            .to_list()
        )
        for e in event_docs:
            if e.execution_id not in latest_by_exec:
                latest_by_exec[e.execution_id] = e

    return flow_doc, layout_doc, flow_exec_doc, block_exec_docs, latest_by_exec
