"""Beanie document models for OpenOMA Server."""

from openoma_server.db.models.execution import (
    BlockExecutionDocument,
    ContractExecutionDocument,
    ExecutionEventDocument,
    FlowExecutionDocument,
)
from openoma_server.db.models.tenant import TenantDocument
from openoma_server.db.models.work_block import (
    ContractDocument,
    FlowDocument,
    WorkBlockDocument,
)

ALL_DOCUMENT_MODELS = [
    WorkBlockDocument,
    FlowDocument,
    ContractDocument,
    ExecutionEventDocument,
    BlockExecutionDocument,
    FlowExecutionDocument,
    ContractExecutionDocument,
    TenantDocument,
]

__all__ = [
    "ALL_DOCUMENT_MODELS",
    "BlockExecutionDocument",
    "ContractDocument",
    "ContractExecutionDocument",
    "ExecutionEventDocument",
    "FlowDocument",
    "FlowExecutionDocument",
    "TenantDocument",
    "WorkBlockDocument",
]
