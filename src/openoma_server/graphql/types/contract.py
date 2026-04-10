from datetime import datetime
from uuid import UUID

import strawberry

from openoma_server.graphql.types.common import JSON


@strawberry.type
class FlowReferenceType:
    flow_id: UUID
    flow_version: int
    alias: str | None
    metadata: JSON


@strawberry.type
class ContractReferenceType:
    contract_id: UUID
    contract_version: int
    alias: str | None
    metadata: JSON


@strawberry.type
class RequiredOutcomeReferenceType:
    required_outcome_id: UUID
    required_outcome_version: int
    alias: str | None
    metadata: JSON


@strawberry.type
class PartyType:
    name: str
    role: str
    contact: str | None


@strawberry.type
class AssessmentBindingType:
    assessment_flow: FlowReferenceType
    test_flow_refs: list[FlowReferenceType]
    metadata: JSON


@strawberry.type
class RequiredOutcomeType:
    id: UUID
    version: int
    created_at: datetime
    created_by: str | None
    name: str
    description: str
    assessment_bindings: list[AssessmentBindingType]
    metadata: JSON


@strawberry.type
class ContractType:
    id: UUID
    version: int
    created_at: datetime
    created_by: str | None
    name: str
    description: str
    owners: list[PartyType]
    work_flows: list[FlowReferenceType]
    sub_contracts: list[ContractReferenceType]
    required_outcomes: list[RequiredOutcomeReferenceType]
    metadata: JSON
