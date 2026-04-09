"""Query resolvers for openoma execution entities."""

from datetime import datetime
from uuid import UUID

import strawberry

from openoma_server.auth.context import AuthContext
from openoma_server.auth.permissions import CanReadExecution
from openoma_server.graphql.types.execution import (
    BlockExecutionSummaryType,
    BlockExecutionType,
    ExecutionEventType,
    FlowExecutionType,
    block_execution_to_type,
    event_to_type,
    flow_execution_to_type,
)
from openoma_server.services import execution as execution_svc


def _get_auth(info: strawberry.Info) -> AuthContext:
    return info.context["auth"]


@strawberry.type
class ExecutionQuery:
    @strawberry.field(permission_classes=[CanReadExecution])
    async def block_execution(
        self,
        info: strawberry.Info,
        execution_id: UUID,
    ) -> BlockExecutionType | None:
        be = await execution_svc.get_block_execution(execution_id, auth=_get_auth(info))
        return block_execution_to_type(be) if be else None

    @strawberry.field(permission_classes=[CanReadExecution])
    async def flow_execution(
        self,
        info: strawberry.Info,
        execution_id: UUID,
    ) -> FlowExecutionType | None:
        fe = await execution_svc.get_flow_execution(execution_id, auth=_get_auth(info))
        return flow_execution_to_type(fe) if fe else None

    @strawberry.field(permission_classes=[CanReadExecution])
    async def execution_events(
        self,
        info: strawberry.Info,
        execution_id: UUID,
        after: datetime | None = None,
    ) -> list[ExecutionEventType]:
        events = await execution_svc.get_execution_events(
            execution_id, after=after, auth=_get_auth(info)
        )
        return [event_to_type(e) for e in events]

    @strawberry.field(permission_classes=[CanReadExecution])
    async def block_executions(
        self,
        info: strawberry.Info,
        flow_execution_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[BlockExecutionSummaryType]:
        summaries = await execution_svc.list_block_executions(
            auth=_get_auth(info),
            flow_execution_id=flow_execution_id,
            limit=limit,
            offset=offset,
        )
        return [
            BlockExecutionSummaryType(
                execution_id=strawberry.ID(str(s["execution_id"])),
                node_reference_id=strawberry.ID(str(s["node_reference_id"])),
                work_block_id=strawberry.ID(str(s["work_block_id"])),
                work_block_version=s["work_block_version"],
                flow_execution_id=(
                    strawberry.ID(str(s["flow_execution_id"])) if s.get("flow_execution_id") else None
                ),
                created_at=s.get("created_at"),
            )
            for s in summaries
        ]
