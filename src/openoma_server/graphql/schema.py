import strawberry

from openoma_server.graphql.mutations.contract import ContractMutation
from openoma_server.graphql.mutations.execution import ExecutionMutation
from openoma_server.graphql.mutations.flow import FlowMutation
from openoma_server.graphql.mutations.work_block import WorkBlockMutation
from openoma_server.graphql.queries.contract import ContractQuery
from openoma_server.graphql.queries.execution import ExecutionQuery
from openoma_server.graphql.queries.flow import FlowQuery
from openoma_server.graphql.queries.work_block import WorkBlockQuery


@strawberry.type
class Query(WorkBlockQuery, FlowQuery, ContractQuery, ExecutionQuery):
    @strawberry.field
    async def health(self) -> str:
        return "ok"


@strawberry.type
class Mutation(WorkBlockMutation, FlowMutation, ContractMutation, ExecutionMutation):
    pass


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
)
