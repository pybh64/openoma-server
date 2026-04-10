from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from openoma_server.auth.context import CurrentUser


class AuthMiddleware(BaseHTTPMiddleware):
    """Auth middleware stub.

    Currently passes all requests through with an anonymous user context.
    Replace the `authenticate` method with real verification (JWT, OAuth, etc.).
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request.state.user = self.authenticate(request)
        return await call_next(request)

    def authenticate(self, request: Request) -> CurrentUser:
        # Stub: extract token from Authorization header when auth is implemented.
        # Example future implementation:
        #   token = request.headers.get("Authorization", "").removeprefix("Bearer ")
        #   if token:
        #       payload = verify_jwt(token)
        #       return CurrentUser(id=payload["sub"], email=payload.get("email"))
        return CurrentUser()
