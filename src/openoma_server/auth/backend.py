"""Pluggable authentication backend protocol and built-in implementations."""

from typing import Protocol, runtime_checkable

from starlette.requests import Request

from openoma_server.auth.context import AuthContext
from openoma_server.settings import settings


@runtime_checkable
class AuthBackend(Protocol):
    """Protocol that any authentication provider must implement.

    Implementations can verify JWTs, validate OAuth2 tokens, check session
    cookies, or any other mechanism. Return None for unauthenticated requests.
    """

    async def authenticate(self, request: Request) -> AuthContext | None: ...


class NoOpAuthBackend:
    """Development/testing backend that bypasses authentication.

    Returns a default service context so the server works without
    any auth infrastructure.
    """

    async def authenticate(self, request: Request) -> AuthContext:
        return AuthContext(
            user_id=settings.default_user_id,
            tenant_id=settings.default_tenant_id,
            attributes={"type": "service", "roles": ["admin"]},
        )


_BACKENDS: dict[str, type[AuthBackend]] = {
    "noop": NoOpAuthBackend,
}


def register_auth_backend(name: str, backend_cls: type[AuthBackend]) -> None:
    """Register a custom auth backend by name for plugin discovery."""
    _BACKENDS[name] = backend_cls


def get_auth_backend() -> AuthBackend:
    """Instantiate the configured auth backend."""
    backend_cls = _BACKENDS.get(settings.auth_backend)
    if backend_cls is None:
        raise ValueError(
            f"Unknown auth backend: {settings.auth_backend!r}. "
            f"Available: {list(_BACKENDS.keys())}"
        )
    return backend_cls()
