"""Contract service — business logic for creating and managing contracts."""

from datetime import UTC, datetime
from uuid import UUID

from openoma.core.contract import Contract
from openoma.core.types import (
    ContractReference,
    FlowReference,
    Party,
    PartyRole,
    RequiredOutcomeReference,
)

from openoma_server.auth.context import CurrentUser
from openoma_server.auth.permissions import check_object_permission
from openoma_server.graphql.inputs.contract import (
    ContractReferenceInput,
    CreateContractInput,
    FlowReferenceInput,
    PartyInput,
    RequiredOutcomeReferenceInput,
    UpdateContractInput,
)
from openoma_server.models.contract import ContractDoc


def _convert_flow_ref(r: FlowReferenceInput) -> FlowReference:
    return FlowReference(
        flow_id=r.flow_id, flow_version=r.flow_version, alias=r.alias, metadata=r.metadata or {}
    )


def _convert_contract_ref(r: ContractReferenceInput) -> ContractReference:
    return ContractReference(
        contract_id=r.contract_id,
        contract_version=r.contract_version,
        alias=r.alias,
        metadata=r.metadata or {},
    )


def _convert_outcome_ref(r: RequiredOutcomeReferenceInput) -> RequiredOutcomeReference:
    return RequiredOutcomeReference(
        required_outcome_id=r.required_outcome_id,
        required_outcome_version=r.required_outcome_version,
        alias=r.alias,
        metadata=r.metadata or {},
    )


def _convert_party(p: PartyInput) -> Party:
    return Party(name=p.name, role=PartyRole(p.role), contact=p.contact)


async def create_contract(input: CreateContractInput, user: CurrentUser) -> ContractDoc:
    entity_id = ContractDoc.new_id()

    contract = Contract(
        id=entity_id,
        version=1,
        created_at=datetime.now(UTC),
        created_by=user.display_name,
        name=input.name,
        description=input.description,
        owners=[_convert_party(p) for p in (input.owners or [])],
        work_flows=[_convert_flow_ref(r) for r in (input.work_flows or [])],
        sub_contracts=[_convert_contract_ref(r) for r in (input.sub_contracts or [])],
        required_outcomes=[_convert_outcome_ref(r) for r in (input.required_outcomes or [])],
        metadata=input.metadata or {},
    )

    doc = ContractDoc.from_core(contract)
    check_object_permission(user, "create", doc)
    await doc.insert()
    return doc


async def update_contract(
    entity_id: UUID, input: UpdateContractInput, user: CurrentUser
) -> ContractDoc:
    latest = await ContractDoc.get_latest(entity_id)
    if latest is None:
        raise ValueError(f"Contract {entity_id} not found")

    check_object_permission(user, "update", latest)
    core = latest.to_core()
    new_version = await ContractDoc.get_next_version(entity_id)

    contract = Contract(
        id=core.id,
        version=new_version,
        created_at=datetime.now(UTC),
        created_by=user.display_name,
        name=input.name if input.name is not None else core.name,
        description=input.description if input.description is not None else core.description,
        owners=(
            [_convert_party(p) for p in input.owners]
            if input.owners is not None
            else list(core.owners)
        ),
        work_flows=(
            [_convert_flow_ref(r) for r in input.work_flows]
            if input.work_flows is not None
            else list(core.work_flows)
        ),
        sub_contracts=(
            [_convert_contract_ref(r) for r in input.sub_contracts]
            if input.sub_contracts is not None
            else list(core.sub_contracts)
        ),
        required_outcomes=(
            [_convert_outcome_ref(r) for r in input.required_outcomes]
            if input.required_outcomes is not None
            else list(core.required_outcomes)
        ),
        metadata=input.metadata if input.metadata is not None else dict(core.metadata),
    )

    doc = ContractDoc.from_core(contract)
    await doc.insert()
    return doc


async def get_contract(entity_id: UUID, version: int | None = None) -> ContractDoc | None:
    if version is not None:
        return await ContractDoc.get_by_version(entity_id, version)
    return await ContractDoc.get_latest(entity_id)


async def list_contracts(
    name: str | None = None, limit: int = 50, offset: int = 0
) -> list[ContractDoc]:
    return await ContractDoc.list_latest(name=name, limit=limit, offset=offset)
