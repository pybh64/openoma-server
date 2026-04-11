from datetime import UTC, datetime
from uuid import UUID, uuid4

from beanie import Document
from openoma.execution.block_execution import BlockExecution
from openoma.execution.contract_execution import ContractExecution
from openoma.execution.events import ExecutionEvent, ExecutionEventType
from openoma.execution.flow_execution import FlowExecution
from openoma.execution.types import ExecutionState
from pymongo import IndexModel

from openoma_server.models.converters import (
    assessment_result_from_doc,
    assessment_result_to_doc,
    execution_outcome_from_doc,
    execution_outcome_to_doc,
    executor_info_from_doc,
    executor_info_to_doc,
)
from openoma_server.models.embedded import (
    AssessmentResultDoc,
    ExecutionOutcomeDoc,
    ExecutorInfoDoc,
)


class ExecutionEventDoc(Document):
    event_id: UUID
    timestamp: datetime = datetime.now(UTC)
    execution_id: UUID
    event_type: str  # ExecutionEventType value
    executor: ExecutorInfoDoc | None = None
    outcome: ExecutionOutcomeDoc | None = None
    metadata: dict = {}

    class Settings:
        name = "execution_events"
        indexes = [
            IndexModel([("execution_id", 1), ("timestamp", 1)]),
            IndexModel([("event_id", 1)], unique=True),
        ]

    def to_core(self) -> ExecutionEvent:
        return ExecutionEvent(
            id=self.event_id,
            timestamp=self.timestamp,
            execution_id=self.execution_id,
            event_type=ExecutionEventType(self.event_type),
            executor=executor_info_from_doc(self.executor) if self.executor else None,
            outcome=execution_outcome_from_doc(self.outcome) if self.outcome else None,
            metadata=self.metadata,
        )

    @classmethod
    def from_core(cls, e: ExecutionEvent) -> "ExecutionEventDoc":
        return cls(
            event_id=e.id,
            timestamp=e.timestamp,
            execution_id=e.execution_id,
            event_type=e.event_type.value,
            executor=executor_info_to_doc(e.executor) if e.executor else None,
            outcome=execution_outcome_to_doc(e.outcome) if e.outcome else None,
            metadata=dict(e.metadata),
        )


class BlockExecutionDoc(Document):
    execution_id: UUID
    flow_execution_id: UUID | None = None
    node_reference_id: UUID
    work_block_id: UUID
    work_block_version: int
    outcome: ExecutionOutcomeDoc | None = None
    state: str = ExecutionState.PENDING.value
    created_at: datetime = datetime.now(UTC)

    class Settings:
        name = "block_executions"
        indexes = [
            IndexModel([("execution_id", 1)], unique=True),
            IndexModel([("flow_execution_id", 1)]),
            IndexModel([("work_block_id", 1)]),
            IndexModel([("state", 1)]),
        ]

    def to_core(self) -> BlockExecution:
        return BlockExecution(
            id=self.execution_id,
            flow_execution_id=self.flow_execution_id,
            node_reference_id=self.node_reference_id,
            work_block_id=self.work_block_id,
            work_block_version=self.work_block_version,
            outcome=execution_outcome_from_doc(self.outcome) if self.outcome else None,
            state=ExecutionState(self.state),
            created_at=self.created_at,
        )

    @classmethod
    def from_core(cls, be: BlockExecution) -> "BlockExecutionDoc":
        return cls(
            execution_id=be.id,
            flow_execution_id=be.flow_execution_id,
            node_reference_id=be.node_reference_id,
            work_block_id=be.work_block_id,
            work_block_version=be.work_block_version,
            outcome=execution_outcome_to_doc(be.outcome) if be.outcome else None,
            state=be.state.value,
            created_at=be.created_at,
        )


class FlowExecutionDoc(Document):
    execution_id: UUID
    contract_execution_id: UUID | None = None
    flow_id: UUID
    flow_version: int
    block_executions: list[UUID] = []
    state: str = ExecutionState.PENDING.value
    created_at: datetime = datetime.now(UTC)

    class Settings:
        name = "flow_executions"
        indexes = [
            IndexModel([("execution_id", 1)], unique=True),
            IndexModel([("flow_id", 1)]),
            IndexModel([("contract_execution_id", 1)]),
            IndexModel([("state", 1)]),
        ]

    def to_core(self) -> FlowExecution:
        return FlowExecution(
            id=self.execution_id,
            contract_execution_id=self.contract_execution_id,
            flow_id=self.flow_id,
            flow_version=self.flow_version,
            block_executions=list(self.block_executions),
            state=ExecutionState(self.state),
            created_at=self.created_at,
        )

    @classmethod
    def from_core(cls, fe: FlowExecution) -> "FlowExecutionDoc":
        return cls(
            execution_id=fe.id,
            contract_execution_id=fe.contract_execution_id,
            flow_id=fe.flow_id,
            flow_version=fe.flow_version,
            block_executions=list(fe.block_executions),
            state=fe.state.value,
            created_at=fe.created_at,
        )


class ContractExecutionDoc(Document):
    execution_id: UUID
    contract_id: UUID
    contract_version: int
    flow_executions: list[UUID] = []
    sub_contract_executions: list[UUID] = []
    assessment_executions: list[AssessmentResultDoc] = []
    state: str = ExecutionState.PENDING.value
    created_at: datetime = datetime.now(UTC)

    class Settings:
        name = "contract_executions"
        indexes = [
            IndexModel([("execution_id", 1)], unique=True),
            IndexModel([("contract_id", 1)]),
            IndexModel([("state", 1)]),
        ]

    def to_core(self) -> ContractExecution:
        return ContractExecution(
            id=self.execution_id,
            contract_id=self.contract_id,
            contract_version=self.contract_version,
            flow_executions=list(self.flow_executions),
            sub_contract_executions=list(self.sub_contract_executions),
            assessment_executions=[
                assessment_result_from_doc(a) for a in self.assessment_executions
            ],
            state=ExecutionState(self.state),
            created_at=self.created_at,
        )

    @classmethod
    def from_core(cls, ce: ContractExecution) -> "ContractExecutionDoc":
        return cls(
            execution_id=ce.id,
            contract_id=ce.contract_id,
            contract_version=ce.contract_version,
            flow_executions=list(ce.flow_executions),
            sub_contract_executions=list(ce.sub_contract_executions),
            assessment_executions=[assessment_result_to_doc(a) for a in ce.assessment_executions],
            state=ce.state.value,
            created_at=ce.created_at,
        )

    @classmethod
    def new_id(cls) -> UUID:
        return uuid4()
