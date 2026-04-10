from typing import Any

from strawberry.permission import BasePermission
from strawberry.types import Info

from openoma_server.auth.context import CurrentUser


class IsAuthenticated(BasePermission):
    """Strawberry permission class. Stub — always grants access.

    Usage on resolvers:
        @strawberry.mutation(permission_classes=[IsAuthenticated])
        async def create_work_block(...) -> WorkBlockType: ...
    """

    message = "Authentication required"

    def has_permission(self, source: Any, info: Info, **kwargs: Any) -> bool:
        # Stub: always allow. When auth is enabled, check info.context.user.is_authenticated
        return True


def check_object_permission(user: CurrentUser, action: str, obj: Any) -> bool:
    """Object-level authorization hook. Stub — always returns True.

    Called in service methods before mutations. When authorization is implemented,
    this will check whether `user` is allowed to perform `action` on `obj`.

    Args:
        user: The current user context.
        action: The action being performed (e.g., "create", "update", "delete", "read").
        obj: The object being acted upon.

    Returns:
        True if the action is allowed.

    Raises:
        PermissionError: When the action is denied (future implementation).
    """
    return True
