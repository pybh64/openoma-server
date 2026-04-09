"""Service layer for Flow CRUD operations."""

from uuid import UUID, uuid4

from openoma import (
    Condition,
    Edge,
    Flow,
    NodeReference,
    PortMapping,
)
from openoma.validation import validate_flow

from openoma_server.auth.context import AuthContext
from openoma_server.db.models import FlowDocument


async def create_flow(
    *,
    name: str,
    description: str = "",
    nodes: list[dict] | None = None,
    edges: list[dict] | None = None,
    expected_outcome: any = None,
    metadata: dict | None = None,
    is_assessment: bool = False,
    auth: AuthContext,
) -> Flow:
    """Create a new Flow and persist it."""
    flow_id = uuid4()
    parsed_nodes = [_parse_node(n) for n in (nodes or [])]
    parsed_edges = [_parse_edge(e) for e in (edges or [])]

    flow = Flow(
        id=flow_id,
        version=1,
        name=name,
        description=description,
        nodes=parsed_nodes,
        edges=parsed_edges,
        expected_outcome=expected_outcome,
        metadata=metadata or {},
    )
    validate_flow(flow, is_assessment=is_assessment)

    doc = FlowDocument(
        flow_id=flow.id,
        version=flow.version,
        name=flow.name,
        description=flow.description,
        nodes=[_node_to_dict(n) for n in flow.nodes],
        edges=[_edge_to_dict(e) for e in flow.edges],
        expected_outcome=flow.expected_outcome,
        metadata=flow.metadata,
        tenant_id=auth.tenant_id,
    )
    await doc.insert()
    return flow


async def get_flow(
    flow_id: UUID, *, version: int | None = None, auth: AuthContext
) -> Flow | None:
    """Retrieve a Flow by ID and optional version."""
    query = {"flow_id": flow_id, "tenant_id": auth.tenant_id}
    if version is not None:
        query["version"] = version
        doc = await FlowDocument.find_one(query)
    else:
        doc = await FlowDocument.find_one(query, sort=[("version", -1)])

    if doc is None:
        return None
    return _doc_to_flow(doc)


async def list_flows(
    *,
    auth: AuthContext,
    name_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
    latest_only: bool = True,
) -> list[Flow]:
    """List Flows for the tenant."""
    if latest_only:
        pipeline: list[dict] = [
            {"$match": {"tenant_id": auth.tenant_id}},
        ]
        if name_filter:
            pipeline[0]["$match"]["name"] = {"$regex": name_filter, "$options": "i"}
        pipeline.extend([
            {"$sort": {"flow_id": 1, "version": -1}},
            {"$group": {"_id": "$flow_id", "doc": {"$first": "$$ROOT"}}},
            {"$replaceRoot": {"newRoot": "$doc"}},
            {"$sort": {"name": 1}},
            {"$skip": offset},
            {"$limit": limit},
        ])
        docs = await FlowDocument.aggregate(pipeline).to_list()
        return [_raw_to_flow(d) for d in docs]

    query: dict = {"tenant_id": auth.tenant_id}
    if name_filter:
        query["name"] = {"$regex": name_filter, "$options": "i"}
    docs = await FlowDocument.find(
        query, sort=[("name", 1)], skip=offset, limit=limit
    ).to_list()
    return [_doc_to_flow(d) for d in docs]


async def update_flow(
    flow_id: UUID,
    *,
    name: str | None = None,
    description: str | None = None,
    nodes: list[dict] | None = None,
    edges: list[dict] | None = None,
    expected_outcome: any = None,
    metadata: dict | None = None,
    is_assessment: bool = False,
    auth: AuthContext,
) -> Flow | None:
    """Create a new version of a Flow with updated fields."""
    current = await get_flow(flow_id, auth=auth)
    if current is None:
        return None

    from openoma.core.versioning import next_version

    overrides: dict = {}
    if name is not None:
        overrides["name"] = name
    if description is not None:
        overrides["description"] = description
    if nodes is not None:
        overrides["nodes"] = [_parse_node(n) for n in nodes]
    if edges is not None:
        overrides["edges"] = [_parse_edge(e) for e in edges]
    if expected_outcome is not None:
        overrides["expected_outcome"] = expected_outcome
    if metadata is not None:
        overrides["metadata"] = metadata

    new_flow = next_version(current, **overrides)
    validate_flow(new_flow, is_assessment=is_assessment)

    doc = FlowDocument(
        flow_id=new_flow.id,
        version=new_flow.version,
        name=new_flow.name,
        description=new_flow.description,
        nodes=[_node_to_dict(n) for n in new_flow.nodes],
        edges=[_edge_to_dict(e) for e in new_flow.edges],
        expected_outcome=new_flow.expected_outcome,
        metadata=new_flow.metadata,
        tenant_id=auth.tenant_id,
    )
    await doc.insert()
    return new_flow


async def delete_flow(
    flow_id: UUID, *, version: int | None = None, auth: AuthContext
) -> int:
    """Delete a Flow (all versions or a specific version). Returns count deleted."""
    query: dict = {"flow_id": flow_id, "tenant_id": auth.tenant_id}
    if version is not None:
        query["version"] = version
    result = await FlowDocument.find(query).delete()
    return result.deleted_count if result else 0


# --- Parsing helpers ---


def _parse_node(data: dict) -> NodeReference:
    return NodeReference(
        id=data.get("id", uuid4()),
        target_id=data["target_id"],
        target_version=data["target_version"],
        alias=data.get("alias"),
        metadata=data.get("metadata", {}),
    )


def _parse_edge(data: dict) -> Edge:
    condition = None
    if data.get("condition"):
        condition = Condition(**data["condition"])
    port_mappings = [PortMapping(**pm) for pm in data.get("port_mappings", [])]
    return Edge(
        source_id=data.get("source_id"),
        target_id=data["target_id"],
        condition=condition,
        port_mappings=port_mappings,
    )


def _node_to_dict(node: NodeReference) -> dict:
    return node.model_dump(mode="json")


def _edge_to_dict(edge: Edge) -> dict:
    return edge.model_dump(mode="json")


def _doc_to_flow(doc: FlowDocument) -> Flow:
    return Flow(
        id=doc.flow_id,
        version=doc.version,
        name=doc.name,
        description=doc.description,
        nodes=[_parse_node(n) for n in doc.nodes],
        edges=[_parse_edge(e) for e in doc.edges],
        expected_outcome=doc.expected_outcome,
        metadata=doc.metadata,
    )


def _raw_to_flow(raw: dict) -> Flow:
    return Flow(
        id=raw["flow_id"],
        version=raw["version"],
        name=raw["name"],
        description=raw.get("description", ""),
        nodes=[_parse_node(n) for n in raw.get("nodes", [])],
        edges=[_parse_edge(e) for e in raw.get("edges", [])],
        expected_outcome=raw.get("expected_outcome"),
        metadata=raw.get("metadata", {}),
    )
