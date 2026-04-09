"""Beanie document model for tenants (organizations)."""

from datetime import UTC, datetime

from beanie import Document
from pydantic import Field


class TenantDocument(Document):
    """An organization/tenant for multi-tenancy isolation."""

    name: str
    description: str = ""
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "tenants"
