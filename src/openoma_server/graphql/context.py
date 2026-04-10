from dataclasses import dataclass

from starlette.requests import Request

from openoma_server.auth.context import CurrentUser


@dataclass
class GraphQLContext:
    request: Request
    user: CurrentUser


async def get_context(request: Request) -> GraphQLContext:
    user = getattr(request.state, "user", CurrentUser())
    return GraphQLContext(request=request, user=user)
