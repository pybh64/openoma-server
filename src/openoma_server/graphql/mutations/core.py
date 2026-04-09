"""Mutation resolvers for openoma core entities."""

from uuid import UUID

import strawberry

from openoma_server.auth.context import AuthContext
from openoma_server.auth.permissions import (
    CanCreateContract,
    CanCreateFlow,
    CanCreateWorkBlock,
    CanDeleteContract,
    CanDeleteFlow,
    CanDeleteWorkBlock,
    CanUpdateContract,
    CanUpdateFlow,
    CanUpdateWorkBlock,
)
from openoma_server.graphql.inputs.core import (
    CreateContractInput,
    CreateFlowInput,
    CreateWorkBlockInput,
    UpdateContractInput,
    UpdateFlowInput,
    UpdateWorkBlockInput,
)
from openoma_server.graphql.types.core import (
    ContractType,
    FlowType,
    WorkBlockType,
    contract_to_type,
    flow_to_type,
    work_block_to_type,
)
from openoma_server.services import contract as contract_svc
from openoma_server.services import flow as flow_svc
from openoma_server.services import work_block as work_block_svc


def _get_auth(info: strawberry.Info) -> AuthContext:
    return info.context["auth"]


def _port_input_to_dict(port) -> dict:
    return {
        "name": port.name,
        "description": port.description,
        "required": port.required,
        "schema": port.schema_def,
        "metadata": port.metadata or {},
    }


def _node_input_to_dict(node) -> dict:
    d = {"target_id": node.target_id, "target_version": node.target_version}
    if node.id is not None:
        d["id"] = node.id
    if node.alias is not None:
        d["alias"] = node.alias
    if node.metadata is not None:
        d["metadata"] = node.metadata
    return d


def _edge_input_to_dict(edge) -> dict:
    d: dict = {"target_id": edge.target_id}
    if edge.source_id is not None:
        d["source_id"] = edge.source_id
    if edge.condition is not None:
        d["condition"] = {
            "description": edge.condition.description,
            "predicate": edge.condition.predicate,
            "metadata": edge.condition.metadata or {},
        }
    if edge.port_mappings:
        d["port_mappings"] = [
            {"source_port": pm.source_port, "target_port": pm.target_port}
            for pm in edge.port_mappings
        ]
    return d


def _flow_ref_to_dict(ref) -> dict:
    d = {"flow_id": ref.flow_id, "flow_version": ref.flow_version}
    if ref.alias is not None:
        d["alias"] = ref.alias
    if ref.metadata is not None:
        d["metadata"] = ref.metadata
    return d


def _contract_ref_to_dict(ref) -> dict:
    d = {"contract_id": ref.contract_id, "contract_version": ref.contract_version}
    if ref.alias is not None:
        d["alias"] = ref.alias
    if ref.metadata is not None:
        d["metadata"] = ref.metadata
    return d


def _outcome_to_dict(outcome) -> dict:
    d = {"name": outcome.name, "description": outcome.description}
    if outcome.id is not None:
        d["id"] = outcome.id
    if outcome.metadata is not None:
        d["metadata"] = outcome.metadata
    return d


def _binding_to_dict(binding) -> dict:
    d = {
        "required_outcome_id": binding.required_outcome_id,
        "assessment_flow_id": binding.assessment_flow_id,
        "assessment_flow_version": binding.assessment_flow_version,
    }
    if binding.test_flow_refs:
        d["test_flow_refs"] = [_flow_ref_to_dict(r) for r in binding.test_flow_refs]
    if binding.metadata is not None:
        d["metadata"] = binding.metadata
    return d


@strawberry.type
class CoreMutation:
    # --- WorkBlock ---

    @strawberry.mutation(permission_classes=[CanCreateWorkBlock])
    async def create_work_block(
        self, info: strawberry.Info, input: CreateWorkBlockInput
    ) -> WorkBlockType:
        block = await work_block_svc.create_work_block(
            name=input.name,
            description=input.description,
            inputs=[_port_input_to_dict(p) for p in input.inputs] if input.inputs else None,
            outputs=[_port_input_to_dict(p) for p in input.outputs] if input.outputs else None,
            execution_hints=input.execution_hints,
            metadata=input.metadata,
            auth=_get_auth(info),
        )
        return work_block_to_type(block)

    @strawberry.mutation(permission_classes=[CanUpdateWorkBlock])
    async def update_work_block(
        self, info: strawberry.Info, input: UpdateWorkBlockInput
    ) -> WorkBlockType | None:
        block = await work_block_svc.update_work_block(
            input.id,
            name=input.name,
            description=input.description,
            inputs=[_port_input_to_dict(p) for p in input.inputs] if input.inputs else None,
            outputs=[_port_input_to_dict(p) for p in input.outputs] if input.outputs else None,
            execution_hints=input.execution_hints,
            metadata=input.metadata,
            auth=_get_auth(info),
        )
        return work_block_to_type(block) if block else None

    @strawberry.mutation(permission_classes=[CanDeleteWorkBlock])
    async def delete_work_block(
        self, info: strawberry.Info, id: UUID, version: int | None = None
    ) -> int:
        return await work_block_svc.delete_work_block(id, version=version, auth=_get_auth(info))

    # --- Flow ---

    @strawberry.mutation(permission_classes=[CanCreateFlow])
    async def create_flow(
        self, info: strawberry.Info, input: CreateFlowInput
    ) -> FlowType:
        flow = await flow_svc.create_flow(
            name=input.name,
            description=input.description,
            nodes=[_node_input_to_dict(n) for n in input.nodes] if input.nodes else None,
            edges=[_edge_input_to_dict(e) for e in input.edges] if input.edges else None,
            expected_outcome=input.expected_outcome,
            metadata=input.metadata,
            is_assessment=input.is_assessment,
            auth=_get_auth(info),
        )
        return flow_to_type(flow)

    @strawberry.mutation(permission_classes=[CanUpdateFlow])
    async def update_flow(
        self, info: strawberry.Info, input: UpdateFlowInput
    ) -> FlowType | None:
        flow = await flow_svc.update_flow(
            input.id,
            name=input.name,
            description=input.description,
            nodes=[_node_input_to_dict(n) for n in input.nodes] if input.nodes else None,
            edges=[_edge_input_to_dict(e) for e in input.edges] if input.edges else None,
            expected_outcome=input.expected_outcome,
            metadata=input.metadata,
            is_assessment=input.is_assessment,
            auth=_get_auth(info),
        )
        return flow_to_type(flow) if flow else None

    @strawberry.mutation(permission_classes=[CanDeleteFlow])
    async def delete_flow(
        self, info: strawberry.Info, id: UUID, version: int | None = None
    ) -> int:
        return await flow_svc.delete_flow(id, version=version, auth=_get_auth(info))

    # --- Contract ---

    @strawberry.mutation(permission_classes=[CanCreateContract])
    async def create_contract(
        self, info: strawberry.Info, input: CreateContractInput
    ) -> ContractType:
        contract = await contract_svc.create_contract(
            name=input.name,
            description=input.description,
            work_flows=(
                [_flow_ref_to_dict(wf) for wf in input.work_flows] if input.work_flows else None
            ),
            sub_contracts=(
                [_contract_ref_to_dict(sc) for sc in input.sub_contracts]
                if input.sub_contracts
                else None
            ),
            required_outcomes=(
                [_outcome_to_dict(ro) for ro in input.required_outcomes]
                if input.required_outcomes
                else None
            ),
            assessment_bindings=(
                [_binding_to_dict(ab) for ab in input.assessment_bindings]
                if input.assessment_bindings
                else None
            ),
            metadata=input.metadata,
            auth=_get_auth(info),
        )
        return contract_to_type(contract)

    @strawberry.mutation(permission_classes=[CanUpdateContract])
    async def update_contract(
        self, info: strawberry.Info, input: UpdateContractInput
    ) -> ContractType | None:
        contract = await contract_svc.update_contract(
            input.id,
            name=input.name,
            description=input.description,
            work_flows=(
                [_flow_ref_to_dict(wf) for wf in input.work_flows] if input.work_flows else None
            ),
            sub_contracts=(
                [_contract_ref_to_dict(sc) for sc in input.sub_contracts]
                if input.sub_contracts
                else None
            ),
            required_outcomes=(
                [_outcome_to_dict(ro) for ro in input.required_outcomes]
                if input.required_outcomes
                else None
            ),
            assessment_bindings=(
                [_binding_to_dict(ab) for ab in input.assessment_bindings]
                if input.assessment_bindings
                else None
            ),
            metadata=input.metadata,
            auth=_get_auth(info),
        )
        return contract_to_type(contract) if contract else None

    @strawberry.mutation(permission_classes=[CanDeleteContract])
    async def delete_contract(
        self, info: strawberry.Info, id: UUID, version: int | None = None
    ) -> int:
        return await contract_svc.delete_contract(id, version=version, auth=_get_auth(info))
