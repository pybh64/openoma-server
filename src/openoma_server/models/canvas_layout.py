from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from beanie import Document
from pydantic import BaseModel, Field
from pymongo import IndexModel


class NodePositionDoc(BaseModel):
    node_reference_id: UUID
    x: float = 0.0
    y: float = 0.0
    width: float | None = None
    height: float | None = None
    metadata: dict = Field(default_factory=dict)


class EdgeLayoutDoc(BaseModel):
    source_id: UUID | None = None
    target_id: UUID
    bend_points: list[dict] = Field(default_factory=list)
    label_position: dict | None = None
    metadata: dict = Field(default_factory=dict)


class CanvasLayoutDoc(Document):
    flow_id: UUID
    flow_version: int
    node_positions: list[NodePositionDoc] = Field(default_factory=list)
    edge_layouts: list[EdgeLayoutDoc] = Field(default_factory=list)
    viewport: dict = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_by: str | None = None

    class Settings:
        name = "canvas_layouts"
        indexes = [
            IndexModel([("flow_id", 1), ("flow_version", 1)], unique=True),
        ]
