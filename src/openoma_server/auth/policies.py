"""ABAC policy engine — decoupled from domain models.

Policies evaluate whether an AuthContext is allowed to perform a given
action on a given resource type. This module is intentionally independent
of Strawberry, FastAPI, or any specific domain model.
"""

from dataclasses import dataclass
from typing import Any

from openoma_server.auth.context import AuthContext


@dataclass
class Policy:
    """A single ABAC policy rule.

    Attributes:
        action: The action being checked (e.g. "read", "create", "delete").
        resource: The resource type (e.g. "work_block", "flow", "contract").
        condition: A callable that receives the AuthContext and optional resource
            attributes, returning True if access is granted.
    """

    action: str
    resource: str
    condition: Any  # Callable[[AuthContext, dict], bool]


class PolicyEngine:
    """Evaluates access policies separate from domain models.

    Follows deny-by-default: if no policy explicitly grants access,
    the request is denied.
    """

    def __init__(self) -> None:
        self._policies: list[Policy] = []

    def add_policy(self, policy: Policy) -> None:
        self._policies.append(policy)

    def evaluate(
        self,
        action: str,
        resource: str,
        context: AuthContext,
        resource_attrs: dict[str, Any] | None = None,
    ) -> bool:
        """Check if the context permits the action on the resource.

        Returns True only if at least one matching policy grants access.
        """
        attrs = resource_attrs or {}
        for policy in self._policies:
            if policy.action in ("*", action) and policy.resource in ("*", resource):
                if policy.condition(context, attrs):
                    return True
        return False


def _admin_condition(ctx: AuthContext, _attrs: dict) -> bool:
    return "admin" in ctx.attributes.get("roles", [])


def _authenticated_read(ctx: AuthContext, _attrs: dict) -> bool:
    return ctx.user_id != ""


def _authenticated_write(ctx: AuthContext, _attrs: dict) -> bool:
    return ctx.user_id != ""


def create_default_policy_engine() -> PolicyEngine:
    """Create a PolicyEngine with sensible defaults.

    Default policies:
    - Admins can do anything.
    - Any authenticated user can read any resource.
    - Any authenticated user can create/update resources.
    """
    engine = PolicyEngine()
    engine.add_policy(Policy(action="*", resource="*", condition=_admin_condition))
    engine.add_policy(Policy(action="read", resource="*", condition=_authenticated_read))
    engine.add_policy(Policy(action="create", resource="*", condition=_authenticated_write))
    engine.add_policy(Policy(action="update", resource="*", condition=_authenticated_write))
    return engine
