"""Relay-style cursor pagination types and cursor encoding utilities."""

from __future__ import annotations

import base64
import json

import strawberry

from openoma_server.graphql.types.contract import ContractType
from openoma_server.graphql.types.execution import (
    BlockExecutionType,
    ContractExecutionType,
    FlowExecutionType,
)
from openoma_server.graphql.types.flow import FlowType
from openoma_server.graphql.types.work_block import WorkBlockType

# ── Cursor utilities ──────────────────────────────────────────────


def encode_cursor(sort_value: str, entity_id: str) -> str:
    """Encode a (sort_value, entity_id) pair into an opaque cursor string."""
    data = json.dumps([sort_value, entity_id])
    return base64.urlsafe_b64encode(data.encode()).decode()


def decode_cursor(cursor: str) -> tuple[str, str]:
    """Decode an opaque cursor string back to (sort_value, entity_id)."""
    data = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
    return (data[0], data[1])


# ── Shared types ──────────────────────────────────────────────────


@strawberry.type
class PageInfo:
    has_next_page: bool
    has_previous_page: bool
    start_cursor: str | None = None
    end_cursor: str | None = None


# ── WorkBlock connection ──────────────────────────────────────────


@strawberry.type
class WorkBlockEdge:
    node: WorkBlockType
    cursor: str


@strawberry.type
class WorkBlockConnection:
    edges: list[WorkBlockEdge]
    page_info: PageInfo
    total_count: int


# ── Flow connection ───────────────────────────────────────────────


@strawberry.type
class FlowEdge:
    node: FlowType
    cursor: str


@strawberry.type
class FlowConnection:
    edges: list[FlowEdge]
    page_info: PageInfo
    total_count: int


# ── Contract connection ───────────────────────────────────────────


@strawberry.type
class ContractEdge:
    node: ContractType
    cursor: str


@strawberry.type
class ContractConnection:
    edges: list[ContractEdge]
    page_info: PageInfo
    total_count: int


# ── BlockExecution connection ─────────────────────────────────────


@strawberry.type
class BlockExecutionEdge:
    node: BlockExecutionType
    cursor: str


@strawberry.type
class BlockExecutionConnection:
    edges: list[BlockExecutionEdge]
    page_info: PageInfo
    total_count: int


# ── FlowExecution connection ─────────────────────────────────────


@strawberry.type
class FlowExecutionEdge:
    node: FlowExecutionType
    cursor: str


@strawberry.type
class FlowExecutionConnection:
    edges: list[FlowExecutionEdge]
    page_info: PageInfo
    total_count: int


# ── ContractExecution connection ──────────────────────────────────


@strawberry.type
class ContractExecutionEdge:
    node: ContractExecutionType
    cursor: str


@strawberry.type
class ContractExecutionConnection:
    edges: list[ContractExecutionEdge]
    page_info: PageInfo
    total_count: int
