"""RequiredOutcome service — business logic for creating and managing required outcomes."""

from datetime import UTC, datetime
from uuid import UUID

from openoma.core.contract import AssessmentBinding, RequiredOutcome
from openoma.core.types import FlowReference

from openoma_server.auth.context import CurrentUser
from openoma_server.auth.permissions import check_object_permission
from openoma_server.graphql.inputs.contract import (
    AssessmentBindingInput,
    CreateRequiredOutcomeInput,
    FlowReferenceInput,
    UpdateRequiredOutcomeInput,
)
from openoma_server.models.contract import RequiredOutcomeDoc


def _convert_flow_ref(r: FlowReferenceInput) -> FlowReference:
    return FlowReference(
        flow_id=r.flow_id,
        flow_version=r.flow_version,
        alias=r.alias,
        metadata=r.metadata or {},
    )


def _convert_assessment_binding(b: AssessmentBindingInput) -> AssessmentBinding:
    return AssessmentBinding(
        assessment_flow=_convert_flow_ref(b.assessment_flow),
        test_flow_refs=[_convert_flow_ref(r) for r in (b.test_flow_refs or [])],
        metadata=b.metadata or {},
    )


async def create_required_outcome(
    input: CreateRequiredOutcomeInput, user: CurrentUser
) -> RequiredOutcomeDoc:
    entity_id = RequiredOutcomeDoc.new_id()

    ro = RequiredOutcome(
        id=entity_id,
        version=1,
        created_at=datetime.now(UTC),
        created_by=user.display_name,
        name=input.name,
        description=input.description,
        assessment_bindings=[
            _convert_assessment_binding(b) for b in (input.assessment_bindings or [])
        ],
        metadata=input.metadata or {},
    )

    doc = RequiredOutcomeDoc.from_core(ro)
    check_object_permission(user, "create", doc)
    await doc.insert()
    return doc


async def update_required_outcome(
    entity_id: UUID, input: UpdateRequiredOutcomeInput, user: CurrentUser
) -> RequiredOutcomeDoc:
    latest = await RequiredOutcomeDoc.get_latest(entity_id)
    if latest is None:
        raise ValueError(f"RequiredOutcome {entity_id} not found")

    check_object_permission(user, "update", latest)
    core = latest.to_core()
    new_version = await RequiredOutcomeDoc.get_next_version(entity_id)

    ro = RequiredOutcome(
        id=core.id,
        version=new_version,
        created_at=datetime.now(UTC),
        created_by=user.display_name,
        name=input.name if input.name is not None else core.name,
        description=input.description if input.description is not None else core.description,
        assessment_bindings=(
            [_convert_assessment_binding(b) for b in input.assessment_bindings]
            if input.assessment_bindings is not None
            else list(core.assessment_bindings)
        ),
        metadata=input.metadata if input.metadata is not None else dict(core.metadata),
    )

    doc = RequiredOutcomeDoc.from_core(ro)
    await doc.insert()
    return doc


async def get_required_outcome(
    entity_id: UUID, version: int | None = None
) -> RequiredOutcomeDoc | None:
    if version is not None:
        return await RequiredOutcomeDoc.get_by_version(entity_id, version)
    return await RequiredOutcomeDoc.get_latest(entity_id)


async def list_required_outcomes(
    name: str | None = None, limit: int = 50, offset: int = 0
) -> list[RequiredOutcomeDoc]:
    return await RequiredOutcomeDoc.list_latest(name=name, limit=limit, offset=offset)
