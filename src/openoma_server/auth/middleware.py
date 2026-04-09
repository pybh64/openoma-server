"""FastAPI middleware for authentication context injection."""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from openoma_server.auth.backend import AuthBackend


class AuthMiddleware(BaseHTTPMiddleware):
    """Extracts authentication credentials and injects AuthContext into request state."""

    def __init__(self, app: any, backend: AuthBackend) -> None:
        super().__init__(app)
        self.backend = backend

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        auth_context = await self.backend.authenticate(request)
        request.state.auth = auth_context
        return await call_next(request)
