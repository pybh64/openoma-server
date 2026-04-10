from openoma_server.models.canvas_layout import CanvasLayoutDoc
from openoma_server.models.contract import ContractDoc, RequiredOutcomeDoc
from openoma_server.models.execution import (
    BlockExecutionDoc,
    ContractExecutionDoc,
    ExecutionEventDoc,
    FlowExecutionDoc,
)
from openoma_server.models.flow import FlowDoc
from openoma_server.models.flow_draft import FlowDraftDoc
from openoma_server.models.work_block import WorkBlockDoc

ALL_DOCUMENT_MODELS = [
    WorkBlockDoc,
    FlowDoc,
    FlowDraftDoc,
    CanvasLayoutDoc,
    ContractDoc,
    RequiredOutcomeDoc,
    ExecutionEventDoc,
    BlockExecutionDoc,
    FlowExecutionDoc,
    ContractExecutionDoc,
]

__all__ = [
    "ALL_DOCUMENT_MODELS",
    "WorkBlockDoc",
    "FlowDoc",
    "FlowDraftDoc",
    "CanvasLayoutDoc",
    "ContractDoc",
    "RequiredOutcomeDoc",
    "ExecutionEventDoc",
    "BlockExecutionDoc",
    "FlowExecutionDoc",
    "ContractExecutionDoc",
]
