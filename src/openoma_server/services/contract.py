"""Service layer for Contract CRUD operations."""

from uuid import UUID, uuid4

from openoma import (
    AssessmentBinding,
    Contract,
    ContractReference,
    FlowReference,
    RequiredOutcome,
)
from openoma.validation import validate_contract

from openoma_server.auth.context import AuthContext
from openoma_server.db.models import ContractDocument


async def create_contract(
    *,
    name: str,
    description: str = "",
    work_flows: list[dict] | None = None,
    sub_contracts: list[dict] | None = None,
    required_outcomes: list[dict] | None = None,
    assessment_bindings: list[dict] | None = None,
    metadata: dict | None = None,
    auth: AuthContext,
) -> Contract:
    """Create a new Contract and persist it."""
    contract_id = uuid4()

    contract = Contract(
        id=contract_id,
        version=1,
        name=name,
        description=description,
        work_flows=[FlowReference(**wf) for wf in (work_flows or [])],
        sub_contracts=[ContractReference(**sc) for sc in (sub_contracts or [])],
        required_outcomes=[_parse_outcome(ro) for ro in (required_outcomes or [])],
        assessment_bindings=[_parse_binding(ab) for ab in (assessment_bindings or [])],
        metadata=metadata or {},
    )
    validate_contract(contract)

    doc = ContractDocument(
        contract_id=contract.id,
        version=contract.version,
        name=contract.name,
        description=contract.description,
        work_flows=[wf.model_dump(mode="json") for wf in contract.work_flows],
        sub_contracts=[sc.model_dump(mode="json") for sc in contract.sub_contracts],
        required_outcomes=[ro.model_dump(mode="json") for ro in contract.required_outcomes],
        assessment_bindings=[ab.model_dump(mode="json") for ab in contract.assessment_bindings],
        metadata=contract.metadata,
        tenant_id=auth.tenant_id,
    )
    await doc.insert()
    return contract


async def get_contract(
    contract_id: UUID, *, version: int | None = None, auth: AuthContext
) -> Contract | None:
    """Retrieve a Contract by ID and optional version."""
    query = {"contract_id": contract_id, "tenant_id": auth.tenant_id}
    if version is not None:
        query["version"] = version
        doc = await ContractDocument.find_one(query)
    else:
        doc = await ContractDocument.find_one(query, sort=[("version", -1)])

    if doc is None:
        return None
    return _doc_to_contract(doc)


async def list_contracts(
    *,
    auth: AuthContext,
    name_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
    latest_only: bool = True,
) -> list[Contract]:
    """List Contracts for the tenant."""
    if latest_only:
        pipeline: list[dict] = [
            {"$match": {"tenant_id": auth.tenant_id}},
        ]
        if name_filter:
            pipeline[0]["$match"]["name"] = {"$regex": name_filter, "$options": "i"}
        pipeline.extend([
            {"$sort": {"contract_id": 1, "version": -1}},
            {"$group": {"_id": "$contract_id", "doc": {"$first": "$$ROOT"}}},
            {"$replaceRoot": {"newRoot": "$doc"}},
            {"$sort": {"name": 1}},
            {"$skip": offset},
            {"$limit": limit},
        ])
        docs = await ContractDocument.aggregate(pipeline).to_list()
        return [_raw_to_contract(d) for d in docs]

    query: dict = {"tenant_id": auth.tenant_id}
    if name_filter:
        query["name"] = {"$regex": name_filter, "$options": "i"}
    docs = await ContractDocument.find(
        query, sort=[("name", 1)], skip=offset, limit=limit
    ).to_list()
    return [_doc_to_contract(d) for d in docs]


async def update_contract(
    contract_id: UUID,
    *,
    name: str | None = None,
    description: str | None = None,
    work_flows: list[dict] | None = None,
    sub_contracts: list[dict] | None = None,
    required_outcomes: list[dict] | None = None,
    assessment_bindings: list[dict] | None = None,
    metadata: dict | None = None,
    auth: AuthContext,
) -> Contract | None:
    """Create a new version of a Contract with updated fields."""
    current = await get_contract(contract_id, auth=auth)
    if current is None:
        return None

    from openoma.core.versioning import next_version

    overrides: dict = {}
    if name is not None:
        overrides["name"] = name
    if description is not None:
        overrides["description"] = description
    if work_flows is not None:
        overrides["work_flows"] = [FlowReference(**wf) for wf in work_flows]
    if sub_contracts is not None:
        overrides["sub_contracts"] = [ContractReference(**sc) for sc in sub_contracts]
    if required_outcomes is not None:
        overrides["required_outcomes"] = [_parse_outcome(ro) for ro in required_outcomes]
    if assessment_bindings is not None:
        overrides["assessment_bindings"] = [_parse_binding(ab) for ab in assessment_bindings]
    if metadata is not None:
        overrides["metadata"] = metadata

    new_contract = next_version(current, **overrides)
    validate_contract(new_contract)

    doc = ContractDocument(
        contract_id=new_contract.id,
        version=new_contract.version,
        name=new_contract.name,
        description=new_contract.description,
        work_flows=[wf.model_dump(mode="json") for wf in new_contract.work_flows],
        sub_contracts=[sc.model_dump(mode="json") for sc in new_contract.sub_contracts],
        required_outcomes=[ro.model_dump(mode="json") for ro in new_contract.required_outcomes],
        assessment_bindings=[
            ab.model_dump(mode="json") for ab in new_contract.assessment_bindings
        ],
        metadata=new_contract.metadata,
        tenant_id=auth.tenant_id,
    )
    await doc.insert()
    return new_contract


async def delete_contract(
    contract_id: UUID, *, version: int | None = None, auth: AuthContext
) -> int:
    """Delete a Contract (all versions or a specific version). Returns count deleted."""
    query: dict = {"contract_id": contract_id, "tenant_id": auth.tenant_id}
    if version is not None:
        query["version"] = version
    result = await ContractDocument.find(query).delete()
    return result.deleted_count if result else 0


# --- Parsing helpers ---


def _parse_outcome(data: dict) -> RequiredOutcome:
    return RequiredOutcome(
        id=data.get("id", uuid4()),
        name=data["name"],
        description=data.get("description", ""),
        metadata=data.get("metadata", {}),
    )


def _parse_binding(data: dict) -> AssessmentBinding:
    test_refs = [FlowReference(**tr) for tr in data.get("test_flow_refs", [])]
    return AssessmentBinding(
        required_outcome_id=data["required_outcome_id"],
        assessment_flow_id=data["assessment_flow_id"],
        assessment_flow_version=data["assessment_flow_version"],
        test_flow_refs=test_refs,
        metadata=data.get("metadata", {}),
    )


def _doc_to_contract(doc: ContractDocument) -> Contract:
    return Contract(
        id=doc.contract_id,
        version=doc.version,
        name=doc.name,
        description=doc.description,
        work_flows=[FlowReference(**wf) for wf in doc.work_flows],
        sub_contracts=[ContractReference(**sc) for sc in doc.sub_contracts],
        required_outcomes=[_parse_outcome(ro) for ro in doc.required_outcomes],
        assessment_bindings=[_parse_binding(ab) for ab in doc.assessment_bindings],
        metadata=doc.metadata,
    )


def _raw_to_contract(raw: dict) -> Contract:
    return Contract(
        id=raw["contract_id"],
        version=raw["version"],
        name=raw["name"],
        description=raw.get("description", ""),
        work_flows=[FlowReference(**wf) for wf in raw.get("work_flows", [])],
        sub_contracts=[ContractReference(**sc) for sc in raw.get("sub_contracts", [])],
        required_outcomes=[_parse_outcome(ro) for ro in raw.get("required_outcomes", [])],
        assessment_bindings=[_parse_binding(ab) for ab in raw.get("assessment_bindings", [])],
        metadata=raw.get("metadata", {}),
    )
