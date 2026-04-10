"""Composite canvas queries that return everything needed to render a flow."""

from __future__ import annotations

from uuid import UUID

import strawberry

from openoma_server.graphql.resolvers import (
    canvas_layout_to_gql,
    execution_event_to_gql,
    flow_execution_to_gql,
    flow_to_gql,
)
from openoma_server.graphql.types.canvas import (
    FlowCanvasData,
    FlowExecutionCanvasData,
    NodeExecutionStateType,
    WorkBlockSummaryType,
)
from openoma_server.graphql.types.execution import ExecutorInfoType
from openoma_server.services.canvas import (
    get_flow_canvas_data,
    get_flow_execution_canvas_data,
)


@strawberry.type
class CanvasQuery:
    @strawberry.field
    async def flow_canvas(
        self, flow_id: UUID, flow_version: int | None = None
    ) -> FlowCanvasData | None:
        result = await get_flow_canvas_data(flow_id, flow_version)
        if result is None:
            return None
        flow_doc, layout_doc, wb_docs = result
        return FlowCanvasData(
            flow=flow_to_gql(flow_doc),
            layout=canvas_layout_to_gql(layout_doc) if layout_doc else None,
            work_block_summaries=[
                WorkBlockSummaryType(
                    id=doc.entity_id,
                    version=doc.version,
                    name=doc.name,
                    description=doc.description,
                    execution_hints=doc.execution_hints,
                )
                for doc in wb_docs
            ],
        )

    @strawberry.field
    async def flow_execution_canvas(
        self, flow_execution_id: UUID
    ) -> FlowExecutionCanvasData | None:
        result = await get_flow_execution_canvas_data(flow_execution_id)
        if result is None:
            return None
        flow_doc, layout_doc, flow_exec_doc, block_exec_docs, latest_events = result

        node_states = []
        for be in block_exec_docs:
            event_doc = latest_events.get(be.execution_id)
            node_states.append(
                NodeExecutionStateType(
                    node_reference_id=be.node_reference_id,
                    block_execution_id=be.execution_id,
                    state=be.state,
                    executor=(
                        ExecutorInfoType(
                            type=event_doc.executor.type,
                            identifier=event_doc.executor.identifier,
                            metadata=event_doc.executor.metadata,
                        )
                        if event_doc and event_doc.executor
                        else None
                    ),
                    latest_event=(
                        execution_event_to_gql(event_doc) if event_doc else None
                    ),
                )
            )

        return FlowExecutionCanvasData(
            flow=flow_to_gql(flow_doc),
            layout=canvas_layout_to_gql(layout_doc) if layout_doc else None,
            execution=flow_execution_to_gql(flow_exec_doc),
            node_states=node_states,
        )
