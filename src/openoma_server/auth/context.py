"""Authentication context carrying user identity and tenant info."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AuthContext:
    """Immutable authentication context injected into every request.

    Attributes:
        user_id: Unique identifier of the authenticated user/service.
        tenant_id: Tenant (organization) the user belongs to.
        attributes: Arbitrary attributes for ABAC evaluation (roles, groups, scopes, etc.).
    """

    user_id: str
    tenant_id: str
    attributes: dict[str, Any] = field(default_factory=dict)

    @property
    def is_service_account(self) -> bool:
        return self.attributes.get("type") == "service"
