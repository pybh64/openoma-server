"""Shared GraphQL scalar types."""

import strawberry

# Re-export strawberry's built-in scalars for convenience
# UUID and datetime are natively supported by Strawberry

# JSON scalar for opaque dict fields
JSON = strawberry.scalars.JSON
