"""Strawberry permission classes that delegate to the ABAC PolicyEngine."""

from typing import Any

import strawberry
from strawberry.permission import BasePermission


class IsAuthenticated(BasePermission):
    """Denies access if there is no authenticated user in context."""

    message = "Authentication required."

    def has_permission(self, source: Any, info: strawberry.Info, **kwargs: Any) -> bool:
        auth_ctx = info.context.get("auth")
        return auth_ctx is not None


class HasAction(BasePermission):
    """Base permission that checks an action against the ABAC PolicyEngine.

    Subclass and set `action` and `resource` class attributes.
    """

    action: str = ""
    resource: str = ""
    message = "Permission denied."

    def has_permission(self, source: Any, info: strawberry.Info, **kwargs: Any) -> bool:
        auth_ctx = info.context.get("auth")
        if auth_ctx is None:
            return False
        policy_engine = info.context.get("policy_engine")
        if policy_engine is None:
            return False
        return policy_engine.evaluate(self.action, self.resource, auth_ctx)


def make_permission(action: str, resource: str) -> type[HasAction]:
    """Factory to create a permission class for a specific action/resource pair."""
    return type(
        f"Can{action.title()}{resource.title().replace('_', '')}",
        (HasAction,),
        {"action": action, "resource": resource, "message": f"Cannot {action} {resource}."},
    )


CanReadWorkBlock = make_permission("read", "work_block")
CanCreateWorkBlock = make_permission("create", "work_block")
CanUpdateWorkBlock = make_permission("update", "work_block")
CanDeleteWorkBlock = make_permission("delete", "work_block")

CanReadFlow = make_permission("read", "flow")
CanCreateFlow = make_permission("create", "flow")
CanUpdateFlow = make_permission("update", "flow")
CanDeleteFlow = make_permission("delete", "flow")

CanReadContract = make_permission("read", "contract")
CanCreateContract = make_permission("create", "contract")
CanUpdateContract = make_permission("update", "contract")
CanDeleteContract = make_permission("delete", "contract")

CanReadExecution = make_permission("read", "execution")
CanCreateExecution = make_permission("create", "execution")
