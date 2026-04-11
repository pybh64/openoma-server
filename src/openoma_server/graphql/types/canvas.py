from __future__ import annotations

from uuid import UUID

import strawberry

from openoma_server.graphql.types.canvas_layout import CanvasLayoutType
from openoma_server.graphql.types.execution import (
    ExecutionEventType,
    ExecutionOutcomeType,
    ExecutorInfoType,
    FlowExecutionType,
)
from openoma_server.graphql.types.flow import FlowType


@strawberry.type
class WorkBlockSummaryType:
    """Lightweight summary of a WorkBlock for canvas rendering."""

    id: UUID
    version: int
    name: str
    description: str
    execution_hints: list[str]


@strawberry.type
class NodeExecutionStateType:
    """Per-node execution state for canvas rendering."""

    node_reference_id: UUID
    block_execution_id: UUID | None = None
    state: str | None = None
    outcome: ExecutionOutcomeType | None = None
    executor: ExecutorInfoType | None = None
    latest_event: ExecutionEventType | None = None


@strawberry.type
class FlowCanvasData:
    """Everything needed to render a flow on the canvas."""

    flow: FlowType
    layout: CanvasLayoutType | None
    work_block_summaries: list[WorkBlockSummaryType]


@strawberry.type
class FlowExecutionCanvasData:
    """Everything needed to render a flow execution on the canvas."""

    flow: FlowType
    layout: CanvasLayoutType | None
    execution: FlowExecutionType
    node_states: list[NodeExecutionStateType]
