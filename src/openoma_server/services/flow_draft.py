"""Flow draft service — business logic for mutable flow drafts."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from openoma.core.flow import Flow
from openoma.validation.graph import validate_flow

from openoma_server.auth.context import CurrentUser
from openoma_server.auth.permissions import check_object_permission
from openoma_server.graphql.inputs.flow import EdgeInput, NodeReferenceInput
from openoma_server.models.embedded import (
    ConditionDoc,
    EdgeDoc,
    NodeReferenceDoc,
    PortMappingDoc,
)
from openoma_server.models.flow import FlowDoc
from openoma_server.models.flow_draft import FlowDraftDoc


def _node_input_to_doc(n: NodeReferenceInput) -> NodeReferenceDoc:
    return NodeReferenceDoc(
        id=n.id or uuid4(),
        target_id=n.target_id,
        target_version=n.target_version,
        alias=n.alias,
        metadata=n.metadata or {},
    )


def _edge_input_to_doc(e: EdgeInput) -> EdgeDoc:
    return EdgeDoc(
        source_id=e.source_id,
        target_id=e.target_id,
        condition=(
            ConditionDoc(
                description=e.condition.description,
                predicate=e.condition.predicate,
                metadata=e.condition.metadata or {},
            )
            if e.condition
            else None
        ),
        port_mappings=[
            PortMappingDoc(source_port=pm.source_port, target_port=pm.target_port)
            for pm in (e.port_mappings or [])
        ],
    )


# ── Lifecycle ─────────────────────────────────────────────────────


async def create_draft_from_flow(
    flow_id: UUID, flow_version: int, user: CurrentUser
) -> FlowDraftDoc:
    """Fork an existing flow version into a mutable draft."""
    flow_doc = await FlowDoc.get_by_version(flow_id, flow_version)
    if flow_doc is None:
        raise ValueError(f"Flow {flow_id} version {flow_version} not found")

    check_object_permission(user, "read", flow_doc)

    doc = FlowDraftDoc(
        draft_id=FlowDraftDoc.new_id(),
        base_flow_id=flow_doc.entity_id,
        base_flow_version=flow_doc.version,
        name=flow_doc.name,
        description=flow_doc.description,
        nodes=list(flow_doc.nodes),
        edges=list(flow_doc.edges),
        expected_outcome=flow_doc.expected_outcome,
        metadata=dict(flow_doc.metadata),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        created_by=user.display_name,
    )
    await doc.insert()
    return doc


async def create_blank_draft(name: str, user: CurrentUser) -> FlowDraftDoc:
    """Create a brand-new empty draft (no base flow)."""
    doc = FlowDraftDoc(
        draft_id=FlowDraftDoc.new_id(),
        name=name,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        created_by=user.display_name,
    )
    await doc.insert()
    return doc


async def get_draft(draft_id: UUID) -> FlowDraftDoc | None:
    return await FlowDraftDoc.find_one(FlowDraftDoc.draft_id == draft_id)


async def list_drafts(
    base_flow_id: UUID | None = None,
    user: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[FlowDraftDoc]:
    filters: list = []
    if base_flow_id is not None:
        filters.append(FlowDraftDoc.base_flow_id == base_flow_id)
    if user is not None:
        filters.append(FlowDraftDoc.created_by == user)
    query = FlowDraftDoc.find(*filters).sort("-updated_at").skip(offset).limit(limit)
    return await query.to_list()


async def discard_draft(draft_id: UUID) -> bool:
    """Delete a draft. Returns True if deleted, False if not found."""
    doc = await get_draft(draft_id)
    if doc is None:
        return False
    await doc.delete()
    return True


async def publish_draft(draft_id: UUID, user: CurrentUser) -> FlowDoc:
    """Convert draft to a new immutable flow version.

    1. Read draft
    2. Build openoma Flow core object
    3. Validate via validate_flow()
    4. If base_flow_id exists: create new version
    5. If no base_flow_id: create version 1
    6. Delete draft
    7. Return new FlowDoc
    """
    draft = await get_draft(draft_id)
    if draft is None:
        raise ValueError(f"Draft {draft_id} not found")

    # Determine entity_id and version
    if draft.base_flow_id is not None:
        entity_id = draft.base_flow_id
        version = await FlowDoc.get_next_version(entity_id)
    else:
        entity_id = FlowDoc.new_id()
        version = 1

    from openoma_server.models.converters import (
        edge_from_doc,
        expected_outcome_from_doc,
        node_ref_from_doc,
    )

    flow = Flow(
        id=entity_id,
        version=version,
        created_at=datetime.now(UTC),
        created_by=user.display_name,
        name=draft.name,
        description=draft.description,
        nodes=[node_ref_from_doc(n) for n in draft.nodes],
        edges=[edge_from_doc(e) for e in draft.edges],
        expected_outcome=(
            expected_outcome_from_doc(draft.expected_outcome) if draft.expected_outcome else None
        ),
        metadata=dict(draft.metadata),
    )

    validate_flow(flow)

    flow_doc = FlowDoc.from_core(flow)
    check_object_permission(user, "create", flow_doc)
    await flow_doc.insert()

    await draft.delete()
    return flow_doc


# ── Granular node operations ──────────────────────────────────────


async def add_node_to_draft(
    draft_id: UUID,
    node: NodeReferenceInput,
    position: dict | None = None,
) -> FlowDraftDoc:
    """Add a single node to the draft."""
    draft = await get_draft(draft_id)
    if draft is None:
        raise ValueError(f"Draft {draft_id} not found")

    node_doc = _node_input_to_doc(node)
    draft.nodes.append(node_doc)

    if position is not None:
        draft.node_positions.append(position)

    draft.updated_at = datetime.now(UTC)
    await draft.save()
    return draft


async def remove_node_from_draft(draft_id: UUID, node_reference_id: UUID) -> FlowDraftDoc:
    """Remove a node and all edges referencing it."""
    draft = await get_draft(draft_id)
    if draft is None:
        raise ValueError(f"Draft {draft_id} not found")

    draft.nodes = [n for n in draft.nodes if n.id != node_reference_id]
    draft.edges = [
        e
        for e in draft.edges
        if e.source_id != node_reference_id and e.target_id != node_reference_id
    ]
    draft.node_positions = [
        p for p in draft.node_positions if p.get("node_reference_id") != str(node_reference_id)
    ]

    draft.updated_at = datetime.now(UTC)
    await draft.save()
    return draft


async def update_node_in_draft(
    draft_id: UUID,
    node_reference_id: UUID,
    alias: str | None = None,
    metadata: dict | None = None,
) -> FlowDraftDoc:
    """Update a node's alias or metadata."""
    draft = await get_draft(draft_id)
    if draft is None:
        raise ValueError(f"Draft {draft_id} not found")

    for node in draft.nodes:
        if node.id == node_reference_id:
            if alias is not None:
                node.alias = alias
            if metadata is not None:
                node.metadata = metadata
            break
    else:
        raise ValueError(f"Node {node_reference_id} not found in draft")

    draft.updated_at = datetime.now(UTC)
    await draft.save()
    return draft


# ── Granular edge operations ──────────────────────────────────────


async def add_edge_to_draft(draft_id: UUID, edge: EdgeInput) -> FlowDraftDoc:
    """Add an edge to the draft. Validates that referenced nodes exist."""
    draft = await get_draft(draft_id)
    if draft is None:
        raise ValueError(f"Draft {draft_id} not found")

    node_ids = {n.id for n in draft.nodes}

    if edge.target_id not in node_ids:
        raise ValueError(f"Edge target_id {edge.target_id} does not reference a node in this draft")

    if edge.source_id is not None and edge.source_id not in node_ids:
        raise ValueError(f"Edge source_id {edge.source_id} does not reference a node in this draft")

    edge_doc = _edge_input_to_doc(edge)
    draft.edges.append(edge_doc)

    draft.updated_at = datetime.now(UTC)
    await draft.save()
    return draft


async def remove_edge_from_draft(
    draft_id: UUID, source_id: UUID | None, target_id: UUID
) -> FlowDraftDoc:
    """Remove an edge identified by (source_id, target_id)."""
    draft = await get_draft(draft_id)
    if draft is None:
        raise ValueError(f"Draft {draft_id} not found")

    draft.edges = [
        e for e in draft.edges if not (e.source_id == source_id and e.target_id == target_id)
    ]

    draft.updated_at = datetime.now(UTC)
    await draft.save()
    return draft


# ── Visual layout operations ──────────────────────────────────────


async def update_node_positions(draft_id: UUID, positions: list[dict]) -> FlowDraftDoc:
    """Batch update node positions."""
    draft = await get_draft(draft_id)
    if draft is None:
        raise ValueError(f"Draft {draft_id} not found")

    draft.node_positions = positions
    draft.updated_at = datetime.now(UTC)
    await draft.save()
    return draft


async def update_viewport(draft_id: UUID, viewport: dict) -> FlowDraftDoc:
    """Update the viewport (pan/zoom)."""
    draft = await get_draft(draft_id)
    if draft is None:
        raise ValueError(f"Draft {draft_id} not found")

    draft.viewport = viewport
    draft.updated_at = datetime.now(UTC)
    await draft.save()
    return draft
