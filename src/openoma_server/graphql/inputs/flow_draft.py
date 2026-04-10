"""GraphQL inputs for flow draft mutations."""

import strawberry

from openoma_server.graphql.types.common import JSON


@strawberry.input
class UpdateNodeInput:
    alias: str | None = None
    metadata: JSON | None = None
