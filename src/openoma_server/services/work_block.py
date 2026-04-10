"""WorkBlock service — business logic for creating and managing work blocks."""

from datetime import UTC, datetime
from uuid import UUID

import strawberry
from openoma.core.types import ExpectedOutcome, PortDescriptor
from openoma.core.work_block import WorkBlock

from openoma_server.auth.context import CurrentUser
from openoma_server.auth.permissions import check_object_permission
from openoma_server.graphql.inputs.work_block import (
    CreateWorkBlockInput,
    ExpectedOutcomeInput,
    PortDescriptorInput,
    UpdateWorkBlockInput,
)
from openoma_server.models.work_block import WorkBlockDoc


def _convert_port_descriptor(p: PortDescriptorInput) -> PortDescriptor:
    return PortDescriptor(
        name=p.name,
        description=p.description,
        required=p.required,
        schema=p.schema_def,
        metadata=p.metadata or {},
    )


def _convert_expected_outcome(e: ExpectedOutcomeInput) -> ExpectedOutcome:
    return ExpectedOutcome(
        name=e.name,
        description=e.description,
        schema=e.schema_def,
        metadata=e.metadata or {},
    )


async def create_work_block(input: CreateWorkBlockInput, user: CurrentUser) -> WorkBlockDoc:
    entity_id = WorkBlockDoc.new_id()

    wb = WorkBlock(
        id=entity_id,
        version=1,
        created_at=datetime.now(UTC),
        created_by=user.display_name,
        name=input.name,
        description=input.description,
        inputs=[_convert_port_descriptor(p) for p in (input.inputs or [])],
        outputs=[_convert_port_descriptor(p) for p in (input.outputs or [])],
        execution_hints=list(input.execution_hints or []),
        expected_outcome=(
            _convert_expected_outcome(input.expected_outcome) if input.expected_outcome else None
        ),
        metadata=input.metadata or {},
    )

    doc = WorkBlockDoc.from_core(wb)
    check_object_permission(user, "create", doc)
    await doc.insert()
    return doc


async def update_work_block(
    entity_id: UUID, input: UpdateWorkBlockInput, user: CurrentUser
) -> WorkBlockDoc:
    latest = await WorkBlockDoc.get_latest(entity_id)
    if latest is None:
        raise ValueError(f"WorkBlock {entity_id} not found")

    check_object_permission(user, "update", latest)
    core = latest.to_core()

    # Build new version with overrides
    new_version = await WorkBlockDoc.get_next_version(entity_id)

    wb = WorkBlock(
        id=core.id,
        version=new_version,
        created_at=datetime.now(UTC),
        created_by=user.display_name,
        name=input.name if input.name is not None else core.name,
        description=input.description if input.description is not None else core.description,
        inputs=(
            [_convert_port_descriptor(p) for p in input.inputs]
            if input.inputs is not None
            else list(core.inputs)
        ),
        outputs=(
            [_convert_port_descriptor(p) for p in input.outputs]
            if input.outputs is not None
            else list(core.outputs)
        ),
        execution_hints=(
            list(input.execution_hints)
            if input.execution_hints is not None
            else list(core.execution_hints)
        ),
        expected_outcome=(
            _convert_expected_outcome(input.expected_outcome)
            if input.expected_outcome is not None and input.expected_outcome is not strawberry.UNSET
            else (core.expected_outcome if input.expected_outcome is strawberry.UNSET else None)
        ),
        metadata=input.metadata if input.metadata is not None else dict(core.metadata),
    )

    doc = WorkBlockDoc.from_core(wb)
    await doc.insert()
    return doc


async def get_work_block(entity_id: UUID, version: int | None = None) -> WorkBlockDoc | None:
    if version is not None:
        return await WorkBlockDoc.get_by_version(entity_id, version)
    return await WorkBlockDoc.get_latest(entity_id)


async def list_work_blocks(
    name: str | None = None, limit: int = 50, offset: int = 0
) -> list[WorkBlockDoc]:
    return await WorkBlockDoc.list_latest(name=name, limit=limit, offset=offset)
