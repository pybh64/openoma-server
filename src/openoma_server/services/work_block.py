"""Service layer for WorkBlock CRUD operations."""

from uuid import UUID, uuid4

from openoma import PortDescriptor, WorkBlock

from openoma_server.auth.context import AuthContext
from openoma_server.db.models import WorkBlockDocument


async def create_work_block(
    *,
    name: str,
    description: str = "",
    inputs: list[dict] | None = None,
    outputs: list[dict] | None = None,
    execution_hints: list[str] | None = None,
    metadata: dict | None = None,
    auth: AuthContext,
) -> WorkBlock:
    """Create a new WorkBlock and persist it."""
    block_id = uuid4()
    input_ports = [PortDescriptor(**p) for p in (inputs or [])]
    output_ports = [PortDescriptor(**p) for p in (outputs or [])]

    block = WorkBlock(
        id=block_id,
        version=1,
        name=name,
        description=description,
        inputs=input_ports,
        outputs=output_ports,
        execution_hints=execution_hints or [],
        metadata=metadata or {},
    )

    doc = WorkBlockDocument(
        block_id=block.id,
        version=block.version,
        name=block.name,
        description=block.description,
        inputs=[p.model_dump(by_alias=True) for p in block.inputs],
        outputs=[p.model_dump(by_alias=True) for p in block.outputs],
        execution_hints=block.execution_hints,
        metadata=block.metadata,
        tenant_id=auth.tenant_id,
    )
    await doc.insert()
    return block


async def get_work_block(
    block_id: UUID, *, version: int | None = None, auth: AuthContext
) -> WorkBlock | None:
    """Retrieve a WorkBlock by ID and optional version."""
    query = {"block_id": block_id, "tenant_id": auth.tenant_id}
    if version is not None:
        query["version"] = version
        doc = await WorkBlockDocument.find_one(query)
    else:
        doc = await WorkBlockDocument.find_one(
            query, sort=[("version", -1)]
        )

    if doc is None:
        return None
    return _doc_to_block(doc)


async def get_work_block_versions(
    block_id: UUID, *, auth: AuthContext
) -> list[WorkBlock]:
    """Retrieve all versions of a WorkBlock."""
    docs = await WorkBlockDocument.find(
        {"block_id": block_id, "tenant_id": auth.tenant_id},
        sort=[("version", 1)],
    ).to_list()
    return [_doc_to_block(d) for d in docs]


async def list_work_blocks(
    *,
    auth: AuthContext,
    name_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
    latest_only: bool = True,
) -> list[WorkBlock]:
    """List WorkBlocks for the tenant, optionally filtered by name."""
    if latest_only:
        pipeline: list[dict] = [
            {"$match": {"tenant_id": auth.tenant_id}},
        ]
        if name_filter:
            pipeline[0]["$match"]["name"] = {"$regex": name_filter, "$options": "i"}
        pipeline.extend([
            {"$sort": {"block_id": 1, "version": -1}},
            {"$group": {"_id": "$block_id", "doc": {"$first": "$$ROOT"}}},
            {"$replaceRoot": {"newRoot": "$doc"}},
            {"$sort": {"name": 1}},
            {"$skip": offset},
            {"$limit": limit},
        ])
        docs = await WorkBlockDocument.aggregate(pipeline).to_list()
        return [_raw_to_block(d) for d in docs]

    query: dict = {"tenant_id": auth.tenant_id}
    if name_filter:
        query["name"] = {"$regex": name_filter, "$options": "i"}
    docs = await WorkBlockDocument.find(
        query, sort=[("name", 1)], skip=offset, limit=limit
    ).to_list()
    return [_doc_to_block(d) for d in docs]


async def update_work_block(
    block_id: UUID,
    *,
    name: str | None = None,
    description: str | None = None,
    inputs: list[dict] | None = None,
    outputs: list[dict] | None = None,
    execution_hints: list[str] | None = None,
    metadata: dict | None = None,
    auth: AuthContext,
) -> WorkBlock | None:
    """Create a new version of a WorkBlock with updated fields."""
    current = await get_work_block(block_id, auth=auth)
    if current is None:
        return None

    from openoma.core.versioning import next_version

    overrides: dict = {}
    if name is not None:
        overrides["name"] = name
    if description is not None:
        overrides["description"] = description
    if inputs is not None:
        overrides["inputs"] = [PortDescriptor(**p) for p in inputs]
    if outputs is not None:
        overrides["outputs"] = [PortDescriptor(**p) for p in outputs]
    if execution_hints is not None:
        overrides["execution_hints"] = execution_hints
    if metadata is not None:
        overrides["metadata"] = metadata

    new_block = next_version(current, **overrides)

    doc = WorkBlockDocument(
        block_id=new_block.id,
        version=new_block.version,
        name=new_block.name,
        description=new_block.description,
        inputs=[p.model_dump(by_alias=True) for p in new_block.inputs],
        outputs=[p.model_dump(by_alias=True) for p in new_block.outputs],
        execution_hints=new_block.execution_hints,
        metadata=new_block.metadata,
        tenant_id=auth.tenant_id,
    )
    await doc.insert()
    return new_block


async def delete_work_block(
    block_id: UUID, *, version: int | None = None, auth: AuthContext
) -> int:
    """Delete a WorkBlock (all versions or a specific version). Returns count deleted."""
    query: dict = {"block_id": block_id, "tenant_id": auth.tenant_id}
    if version is not None:
        query["version"] = version
    result = await WorkBlockDocument.find(query).delete()
    return result.deleted_count if result else 0


def _doc_to_block(doc: WorkBlockDocument) -> WorkBlock:
    return WorkBlock(
        id=doc.block_id,
        version=doc.version,
        name=doc.name,
        description=doc.description,
        inputs=[PortDescriptor(**p) for p in doc.inputs],
        outputs=[PortDescriptor(**p) for p in doc.outputs],
        execution_hints=doc.execution_hints,
        metadata=doc.metadata,
    )


def _raw_to_block(raw: dict) -> WorkBlock:
    return WorkBlock(
        id=raw["block_id"],
        version=raw["version"],
        name=raw["name"],
        description=raw.get("description", ""),
        inputs=[PortDescriptor(**p) for p in raw.get("inputs", [])],
        outputs=[PortDescriptor(**p) for p in raw.get("outputs", [])],
        execution_hints=raw.get("execution_hints", []),
        metadata=raw.get("metadata", {}),
    )
