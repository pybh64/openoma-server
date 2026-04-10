from pydantic import BaseModel


class CurrentUser(BaseModel):
    """Represents the authenticated user. Stub — always anonymous until auth is implemented."""

    id: str = "anonymous"
    email: str | None = None
    roles: list[str] = []

    @property
    def is_authenticated(self) -> bool:
        return self.id != "anonymous"

    @property
    def display_name(self) -> str:
        return self.email or self.id


# Stub: always returns an anonymous user.
# Replace with JWT/OAuth verification when auth is implemented.
def get_current_user() -> CurrentUser:
    return CurrentUser()
