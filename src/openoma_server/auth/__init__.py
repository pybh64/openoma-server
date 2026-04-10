"""Auth stubs — provisioned for future authentication/authorization."""

from openoma_server.auth.context import CurrentUser, get_current_user
from openoma_server.auth.permissions import IsAuthenticated, check_object_permission

__all__ = [
    "CurrentUser",
    "get_current_user",
    "IsAuthenticated",
    "check_object_permission",
]
