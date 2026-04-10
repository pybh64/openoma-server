"""Filter inputs and ordering enums for cursor-paginated queries."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

import strawberry


@strawberry.enum
class OrderDirection(Enum):
    ASC = "asc"
    DESC = "desc"


@strawberry.enum
class WorkBlockOrderBy(Enum):
    CREATED_AT = "created_at"
    NAME = "name"


@strawberry.enum
class FlowOrderBy(Enum):
    CREATED_AT = "created_at"
    NAME = "name"


@strawberry.enum
class ContractOrderBy(Enum):
    CREATED_AT = "created_at"
    NAME = "name"


@strawberry.enum
class ExecutionOrderByField(Enum):
    CREATED_AT = "created_at"


@strawberry.input
class WorkBlockFilter:
    name: str | None = None
    created_by: str | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None


@strawberry.input
class FlowFilter:
    name: str | None = None
    created_by: str | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None


@strawberry.input
class ContractFilter:
    name: str | None = None
    created_by: str | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None


@strawberry.input
class BlockExecutionFilter:
    work_block_id: strawberry.ID | None = None
    flow_execution_id: strawberry.ID | None = None
    state: str | None = None


@strawberry.input
class FlowExecutionFilter:
    flow_id: strawberry.ID | None = None
    contract_execution_id: strawberry.ID | None = None
    state: str | None = None


@strawberry.input
class ContractExecutionFilter:
    contract_id: strawberry.ID | None = None
    state: str | None = None
