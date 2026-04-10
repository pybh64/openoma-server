from uuid import UUID

import strawberry

from openoma_server.graphql.types.common import JSON


@strawberry.input
class FlowReferenceInput:
    flow_id: UUID
    flow_version: int
    alias: str | None = None
    metadata: JSON | None = None


@strawberry.input
class ContractReferenceInput:
    contract_id: UUID
    contract_version: int
    alias: str | None = None
    metadata: JSON | None = None


@strawberry.input
class RequiredOutcomeReferenceInput:
    required_outcome_id: UUID
    required_outcome_version: int
    alias: str | None = None
    metadata: JSON | None = None


@strawberry.input
class PartyInput:
    name: str
    role: str  # "lead", "delegate", "approver", "reviewer"
    contact: str | None = None


@strawberry.input
class AssessmentBindingInput:
    assessment_flow: FlowReferenceInput
    test_flow_refs: list[FlowReferenceInput] | None = None
    metadata: JSON | None = None


@strawberry.input
class CreateRequiredOutcomeInput:
    name: str
    description: str = ""
    assessment_bindings: list[AssessmentBindingInput] | None = None
    metadata: JSON | None = None


@strawberry.input
class UpdateRequiredOutcomeInput:
    name: str | None = None
    description: str | None = None
    assessment_bindings: list[AssessmentBindingInput] | None = None
    metadata: JSON | None = None


@strawberry.input
class CreateContractInput:
    name: str
    description: str = ""
    owners: list[PartyInput] | None = None
    work_flows: list[FlowReferenceInput] | None = None
    sub_contracts: list[ContractReferenceInput] | None = None
    required_outcomes: list[RequiredOutcomeReferenceInput] | None = None
    metadata: JSON | None = None


@strawberry.input
class UpdateContractInput:
    name: str | None = None
    description: str | None = None
    owners: list[PartyInput] | None = None
    work_flows: list[FlowReferenceInput] | None = None
    sub_contracts: list[ContractReferenceInput] | None = None
    required_outcomes: list[RequiredOutcomeReferenceInput] | None = None
    metadata: JSON | None = None
