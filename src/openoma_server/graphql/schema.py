import strawberry

from openoma_server.graphql.mutations.canvas_layout import CanvasLayoutMutation
from openoma_server.graphql.mutations.contract import ContractMutation
from openoma_server.graphql.mutations.execution import ExecutionMutation
from openoma_server.graphql.mutations.flow import FlowMutation
from openoma_server.graphql.mutations.flow_draft import FlowDraftMutation
from openoma_server.graphql.mutations.work_block import WorkBlockMutation
from openoma_server.graphql.queries.canvas import CanvasQuery
from openoma_server.graphql.queries.canvas_layout import CanvasLayoutQuery
from openoma_server.graphql.queries.contract import ContractQuery
from openoma_server.graphql.queries.execution import ExecutionQuery
from openoma_server.graphql.queries.flow import FlowQuery
from openoma_server.graphql.queries.flow_draft import FlowDraftQuery
from openoma_server.graphql.queries.work_block import WorkBlockQuery


@strawberry.type
class Query(
    WorkBlockQuery, FlowQuery, FlowDraftQuery, ContractQuery, ExecutionQuery,
    CanvasLayoutQuery, CanvasQuery
):
    @strawberry.field
    async def health(self) -> str:
        return "ok"


@strawberry.type
class Mutation(
    WorkBlockMutation,
    FlowMutation,
    FlowDraftMutation,
    ContractMutation,
    ExecutionMutation,
    CanvasLayoutMutation,
):
    pass


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
)
