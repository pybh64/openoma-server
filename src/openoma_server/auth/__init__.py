"""Authentication and authorization plugin system."""

from openoma_server.auth.backend import (
    AuthBackend,
    NoOpAuthBackend,
    get_auth_backend,
    register_auth_backend,
)
from openoma_server.auth.context import AuthContext
from openoma_server.auth.middleware import AuthMiddleware
from openoma_server.auth.policies import PolicyEngine, create_default_policy_engine

__all__ = [
    "AuthBackend",
    "AuthContext",
    "AuthMiddleware",
    "NoOpAuthBackend",
    "PolicyEngine",
    "create_default_policy_engine",
    "get_auth_backend",
    "register_auth_backend",
]
