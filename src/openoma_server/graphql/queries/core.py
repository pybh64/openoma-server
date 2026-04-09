"""Query resolvers for openoma core entities."""

from uuid import UUID

import strawberry

from openoma_server.auth.context import AuthContext
from openoma_server.auth.permissions import CanReadContract, CanReadFlow, CanReadWorkBlock
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


@strawberry.type
class CoreQuery:
    @strawberry.field(permission_classes=[CanReadWorkBlock])
    async def work_block(
        self,
        info: strawberry.Info,
        id: UUID,
        version: int | None = None,
    ) -> WorkBlockType | None:
        block = await work_block_svc.get_work_block(id, version=version, auth=_get_auth(info))
        return work_block_to_type(block) if block else None

    @strawberry.field(permission_classes=[CanReadWorkBlock])
    async def work_blocks(
        self,
        info: strawberry.Info,
        name_filter: str | None = None,
        limit: int = 50,
        offset: int = 0,
        latest_only: bool = True,
    ) -> list[WorkBlockType]:
        blocks = await work_block_svc.list_work_blocks(
            auth=_get_auth(info),
            name_filter=name_filter,
            limit=limit,
            offset=offset,
            latest_only=latest_only,
        )
        return [work_block_to_type(b) for b in blocks]

    @strawberry.field(permission_classes=[CanReadWorkBlock])
    async def work_block_versions(
        self,
        info: strawberry.Info,
        id: UUID,
    ) -> list[WorkBlockType]:
        blocks = await work_block_svc.get_work_block_versions(id, auth=_get_auth(info))
        return [work_block_to_type(b) for b in blocks]

    @strawberry.field(permission_classes=[CanReadFlow])
    async def flow(
        self,
        info: strawberry.Info,
        id: UUID,
        version: int | None = None,
    ) -> FlowType | None:
        f = await flow_svc.get_flow(id, version=version, auth=_get_auth(info))
        return flow_to_type(f) if f else None

    @strawberry.field(permission_classes=[CanReadFlow])
    async def flows(
        self,
        info: strawberry.Info,
        name_filter: str | None = None,
        limit: int = 50,
        offset: int = 0,
        latest_only: bool = True,
    ) -> list[FlowType]:
        flows = await flow_svc.list_flows(
            auth=_get_auth(info),
            name_filter=name_filter,
            limit=limit,
            offset=offset,
            latest_only=latest_only,
        )
        return [flow_to_type(f) for f in flows]

    @strawberry.field(permission_classes=[CanReadContract])
    async def contract(
        self,
        info: strawberry.Info,
        id: UUID,
        version: int | None = None,
    ) -> ContractType | None:
        c = await contract_svc.get_contract(id, version=version, auth=_get_auth(info))
        return contract_to_type(c) if c else None

    @strawberry.field(permission_classes=[CanReadContract])
    async def contracts(
        self,
        info: strawberry.Info,
        name_filter: str | None = None,
        limit: int = 50,
        offset: int = 0,
        latest_only: bool = True,
    ) -> list[ContractType]:
        contracts = await contract_svc.list_contracts(
            auth=_get_auth(info),
            name_filter=name_filter,
            limit=limit,
            offset=offset,
            latest_only=latest_only,
        )
        return [contract_to_type(c) for c in contracts]
