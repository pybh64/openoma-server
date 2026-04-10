from dataclasses import dataclass, field
from functools import cached_property
from uuid import UUID

from strawberry.dataloader import DataLoader
from strawberry.fastapi import BaseContext

from openoma_server.auth.context import CurrentUser
from openoma_server.models.execution import (
    BlockExecutionDoc,
    ContractExecutionDoc,
    FlowExecutionDoc,
)
from openoma_server.store.definition_store import MongoDefinitionStore
from openoma_server.store.event_store import MongoEventStore
from openoma_server.store.execution_store import MongoExecutionStore

# Singleton store instances
_definition_store = MongoDefinitionStore()
_event_store = MongoEventStore()
_execution_store = MongoExecutionStore()


@dataclass
class GraphQLContext(BaseContext):
    user: CurrentUser = field(default_factory=CurrentUser)
    definition_store: MongoDefinitionStore = field(default_factory=lambda: _definition_store)
    event_store: MongoEventStore = field(default_factory=lambda: _event_store)
    execution_store: MongoExecutionStore = field(default_factory=lambda: _execution_store)

    @cached_property
    def work_block_loader(self) -> DataLoader:
        async def load_fn(keys: list[tuple[UUID, int]]):
            blocks = await self.definition_store.get_work_blocks(list(keys))
            by_key = {(b.id, b.version): b for b in blocks}
            return [by_key.get(k) for k in keys]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def flow_loader(self) -> DataLoader:
        async def load_fn(keys: list[tuple[UUID, int]]):
            flows = await self.definition_store.get_flows(list(keys))
            by_key = {(f.id, f.version): f for f in flows}
            return [by_key.get(k) for k in keys]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def block_execution_loader(self) -> DataLoader:
        async def load_fn(keys: list[UUID]):
            docs = await BlockExecutionDoc.find(
                {"execution_id": {"$in": list(keys)}}
            ).to_list()
            by_id = {doc.execution_id: doc for doc in docs}
            return [by_id.get(k) for k in keys]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def flow_execution_loader(self) -> DataLoader:
        async def load_fn(keys: list[UUID]):
            docs = await FlowExecutionDoc.find(
                {"execution_id": {"$in": list(keys)}}
            ).to_list()
            by_id = {doc.execution_id: doc for doc in docs}
            return [by_id.get(k) for k in keys]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def contract_execution_loader(self) -> DataLoader:
        async def load_fn(keys: list[UUID]):
            docs = await ContractExecutionDoc.find(
                {"execution_id": {"$in": list(keys)}}
            ).to_list()
            by_id = {doc.execution_id: doc for doc in docs}
            return [by_id.get(k) for k in keys]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def event_loader(self) -> DataLoader:
        async def load_fn(keys: list[UUID]):
            events = await self.event_store.get_latest_events(list(keys))
            by_id = {e.execution_id: e for e in events}
            return [by_id.get(k) for k in keys]

        return DataLoader(load_fn=load_fn)


async def get_context() -> GraphQLContext:
    return GraphQLContext()
