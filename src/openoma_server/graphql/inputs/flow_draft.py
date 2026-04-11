"""GraphQL inputs for flow draft mutations."""

from uuid import UUID

import strawberry

from openoma_server.graphql.types.common import JSON


@strawberry.input
class UpdateNodeInput:
    target_id: UUID | None = None
    target_version: int | None = None
    alias: str | None = None
    execution_schedule: str | None = None
    metadata: JSON | None = None
