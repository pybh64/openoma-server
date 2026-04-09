"""Root GraphQL schema combining all queries, mutations, and subscriptions."""

import strawberry

from openoma_server.graphql.queries.core import CoreQuery
from openoma_server.graphql.queries.execution import ExecutionQuery
from openoma_server.graphql.mutations.core import CoreMutation
from openoma_server.graphql.mutations.execution import ExecutionMutation
from openoma_server.graphql.subscriptions.execution import Subscription


@strawberry.type
class Query(CoreQuery, ExecutionQuery):
    """Root query type combining core and execution queries."""

    pass


@strawberry.type
class Mutation(CoreMutation, ExecutionMutation):
    """Root mutation type combining core and execution mutations."""

    pass


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
)
