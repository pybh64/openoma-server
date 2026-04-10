from uuid import UUID

import strawberry

from openoma_server.graphql.resolvers import work_block_to_gql
from openoma_server.graphql.types.work_block import WorkBlockType
from openoma_server.services import work_block as wb_service


@strawberry.type
class WorkBlockQuery:
    @strawberry.field
    async def work_block(self, id: UUID, version: int | None = None) -> WorkBlockType | None:
        doc = await wb_service.get_work_block(id, version)
        return work_block_to_gql(doc) if doc else None

    @strawberry.field
    async def work_blocks(
        self,
        name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[WorkBlockType]:
        docs = await wb_service.list_work_blocks(name=name, limit=limit, offset=offset)
        return [work_block_to_gql(d) for d in docs]
