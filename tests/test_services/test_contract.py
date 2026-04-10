"""Tests for the Contract and RequiredOutcome service layers."""

from uuid import uuid4

import pytest

from openoma_server.auth.context import CurrentUser
from openoma_server.graphql.inputs.contract import (
    AssessmentBindingInput,
    ContractReferenceInput,
    CreateContractInput,
    CreateRequiredOutcomeInput,
    FlowReferenceInput,
    PartyInput,
    RequiredOutcomeReferenceInput,
    UpdateContractInput,
    UpdateRequiredOutcomeInput,
)
from openoma_server.services.contract import (
    create_contract,
    get_contract,
    list_contracts,
    update_contract,
)
from openoma_server.services.required_outcome import (
    create_required_outcome,
    get_required_outcome,
    list_required_outcomes,
    update_required_outcome,
)

pytestmark = pytest.mark.asyncio

USER = CurrentUser(id="test-user", email="test@example.com")


# ── RequiredOutcome Tests ──────────────────────────────────────────


async def test_create_required_outcome_minimal():
    doc = await create_required_outcome(CreateRequiredOutcomeInput(name="Quality Check"), USER)
    assert doc.name == "Quality Check"
    assert doc.version == 1
    assert doc.assessment_bindings == []


async def test_create_required_outcome_with_bindings():
    flow_id = uuid4()
    test_flow_id = uuid4()

    doc = await create_required_outcome(
        CreateRequiredOutcomeInput(
            name="Compliance Check",
            description="Ensures regulatory compliance",
            assessment_bindings=[
                AssessmentBindingInput(
                    assessment_flow=FlowReferenceInput(
                        flow_id=flow_id, flow_version=1, alias="assess"
                    ),
                    test_flow_refs=[
                        FlowReferenceInput(flow_id=test_flow_id, flow_version=1, alias="test")
                    ],
                    metadata={"weight": 0.8},
                )
            ],
            metadata={"category": "regulatory"},
        ),
        USER,
    )
    assert len(doc.assessment_bindings) == 1
    assert doc.assessment_bindings[0].assessment_flow.flow_id == flow_id
    assert len(doc.assessment_bindings[0].test_flow_refs) == 1
    assert doc.metadata["category"] == "regulatory"


async def test_update_required_outcome():
    doc = await create_required_outcome(CreateRequiredOutcomeInput(name="Original Outcome"), USER)
    updated = await update_required_outcome(
        doc.entity_id,
        UpdateRequiredOutcomeInput(name="Updated Outcome"),
        USER,
    )
    assert updated.entity_id == doc.entity_id
    assert updated.version == 2
    assert updated.name == "Updated Outcome"


async def test_update_required_outcome_partial():
    doc = await create_required_outcome(
        CreateRequiredOutcomeInput(name="Keep", description="Original"), USER
    )
    updated = await update_required_outcome(
        doc.entity_id,
        UpdateRequiredOutcomeInput(description="Changed"),
        USER,
    )
    assert updated.name == "Keep"
    assert updated.description == "Changed"


async def test_update_nonexistent_outcome_raises():
    with pytest.raises(ValueError, match="not found"):
        await update_required_outcome(uuid4(), UpdateRequiredOutcomeInput(name="x"), USER)


async def test_get_required_outcome():
    doc = await create_required_outcome(CreateRequiredOutcomeInput(name="Fetchable"), USER)
    fetched = await get_required_outcome(doc.entity_id)
    assert fetched is not None
    assert fetched.name == "Fetchable"


async def test_get_required_outcome_version():
    doc = await create_required_outcome(CreateRequiredOutcomeInput(name="V1 Outcome"), USER)
    await update_required_outcome(
        doc.entity_id, UpdateRequiredOutcomeInput(name="V2 Outcome"), USER
    )

    v1 = await get_required_outcome(doc.entity_id, version=1)
    assert v1 is not None
    assert v1.name == "V1 Outcome"


async def test_list_required_outcomes():
    await create_required_outcome(CreateRequiredOutcomeInput(name="Outcome A"), USER)
    await create_required_outcome(CreateRequiredOutcomeInput(name="Outcome B"), USER)
    results = await list_required_outcomes()
    assert len(results) >= 2


# ── Contract Tests ─────────────────────────────────────────────────


async def test_create_contract_minimal():
    doc = await create_contract(CreateContractInput(name="Simple Contract"), USER)
    assert doc.name == "Simple Contract"
    assert doc.version == 1
    assert doc.created_by == "test@example.com"


async def test_create_contract_with_owners():
    doc = await create_contract(
        CreateContractInput(
            name="Owned Contract",
            owners=[
                PartyInput(name="Alice", role="lead", contact="alice@example.com"),
                PartyInput(name="Bob", role="reviewer"),
            ],
        ),
        USER,
    )
    assert len(doc.owners) == 2
    assert doc.owners[0].name == "Alice"
    assert doc.owners[0].role == "lead"
    assert doc.owners[1].name == "Bob"


async def test_create_contract_with_flow_refs():
    flow_id = uuid4()
    doc = await create_contract(
        CreateContractInput(
            name="Flow Contract",
            work_flows=[FlowReferenceInput(flow_id=flow_id, flow_version=1, alias="main-flow")],
        ),
        USER,
    )
    assert len(doc.work_flows) == 1
    assert doc.work_flows[0].flow_id == flow_id
    assert doc.work_flows[0].alias == "main-flow"


async def test_create_contract_with_sub_contracts():
    sub_id = uuid4()
    doc = await create_contract(
        CreateContractInput(
            name="Parent Contract",
            sub_contracts=[
                ContractReferenceInput(contract_id=sub_id, contract_version=1, alias="sub")
            ],
        ),
        USER,
    )
    assert len(doc.sub_contracts) == 1
    assert doc.sub_contracts[0].contract_id == sub_id


async def test_create_contract_with_required_outcomes():
    ro_id = uuid4()
    doc = await create_contract(
        CreateContractInput(
            name="Outcome Contract",
            required_outcomes=[
                RequiredOutcomeReferenceInput(
                    required_outcome_id=ro_id,
                    required_outcome_version=1,
                    alias="quality",
                )
            ],
        ),
        USER,
    )
    assert len(doc.required_outcomes) == 1
    assert doc.required_outcomes[0].required_outcome_id == ro_id


async def test_create_full_contract():
    """Contract with all fields populated."""
    doc = await create_contract(
        CreateContractInput(
            name="Full Contract",
            description="A complete contract",
            owners=[PartyInput(name="Manager", role="lead")],
            work_flows=[FlowReferenceInput(flow_id=uuid4(), flow_version=1)],
            sub_contracts=[ContractReferenceInput(contract_id=uuid4(), contract_version=1)],
            required_outcomes=[
                RequiredOutcomeReferenceInput(
                    required_outcome_id=uuid4(), required_outcome_version=1
                )
            ],
            metadata={"priority": "high"},
        ),
        USER,
    )
    assert doc.name == "Full Contract"
    assert len(doc.owners) == 1
    assert len(doc.work_flows) == 1
    assert len(doc.sub_contracts) == 1
    assert len(doc.required_outcomes) == 1
    assert doc.metadata["priority"] == "high"


async def test_update_contract_creates_new_version():
    doc = await create_contract(CreateContractInput(name="V1 Contract"), USER)
    updated = await update_contract(
        doc.entity_id,
        UpdateContractInput(name="V2 Contract"),
        USER,
    )
    assert updated.entity_id == doc.entity_id
    assert updated.version == 2
    assert updated.name == "V2 Contract"


async def test_update_contract_partial():
    doc = await create_contract(CreateContractInput(name="Keep Name", description="Original"), USER)
    updated = await update_contract(
        doc.entity_id,
        UpdateContractInput(description="Updated"),
        USER,
    )
    assert updated.name == "Keep Name"
    assert updated.description == "Updated"


async def test_update_nonexistent_contract_raises():
    with pytest.raises(ValueError, match="not found"):
        await update_contract(uuid4(), UpdateContractInput(name="x"), USER)


async def test_get_contract_latest():
    doc = await create_contract(CreateContractInput(name="GetLatest"), USER)
    await update_contract(doc.entity_id, UpdateContractInput(name="GetLatest v2"), USER)
    latest = await get_contract(doc.entity_id)
    assert latest is not None
    assert latest.version == 2


async def test_get_contract_specific_version():
    doc = await create_contract(CreateContractInput(name="Pinned V1"), USER)
    await update_contract(doc.entity_id, UpdateContractInput(name="Pinned V2"), USER)
    v1 = await get_contract(doc.entity_id, version=1)
    assert v1 is not None
    assert v1.name == "Pinned V1"


async def test_get_contract_not_found():
    result = await get_contract(uuid4())
    assert result is None


async def test_list_contracts():
    await create_contract(CreateContractInput(name="Contract Alpha"), USER)
    await create_contract(CreateContractInput(name="Contract Beta"), USER)

    results = await list_contracts()
    assert len(results) >= 2


async def test_list_contracts_name_filter():
    await create_contract(CreateContractInput(name="UniqueContractXYZ"), USER)
    results = await list_contracts(name="UniqueContractXYZ")
    assert len(results) >= 1


async def test_list_contracts_returns_latest_only():
    doc = await create_contract(CreateContractInput(name="VersionedContract"), USER)
    await update_contract(
        doc.entity_id,
        UpdateContractInput(name="VersionedContract v2"),
        USER,
    )
    results = await list_contracts(name="VersionedContract")
    matching = [r for r in results if r.entity_id == doc.entity_id]
    assert len(matching) == 1
    assert matching[0].version == 2


async def test_contract_roundtrip_to_core():
    doc = await create_contract(
        CreateContractInput(
            name="Roundtrip",
            owners=[PartyInput(name="Lead", role="lead")],
            work_flows=[FlowReferenceInput(flow_id=uuid4(), flow_version=1)],
            metadata={"test": True},
        ),
        USER,
    )
    core = doc.to_core()
    assert core.name == "Roundtrip"
    assert len(core.owners) == 1
    assert core.owners[0].name == "Lead"
    assert core.metadata["test"] is True
