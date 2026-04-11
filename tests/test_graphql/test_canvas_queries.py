"""Tests for composite canvas queries via the GraphQL schema."""

import uuid

import pytest

from openoma_server.graphql.schema import schema
from openoma_server.models.canvas_layout import CanvasLayoutDoc, NodePositionDoc
from openoma_server.models.embedded import ExecutorInfoDoc
from openoma_server.models.execution import BlockExecutionDoc, ExecutionEventDoc, FlowExecutionDoc

pytestmark = pytest.mark.asyncio

CREATE_WORK_BLOCK = """
mutation CreateWorkBlock($input: CreateWorkBlockInput!) {
  createWorkBlock(input: $input) {
    id
    version
    name
  }
}
"""

CREATE_FLOW = """
mutation CreateFlow($input: CreateFlowInput!) {
  createFlow(input: $input) {
    id
    version
    name
  }
}
"""

FLOW_CANVAS = """
query FlowCanvas($flowId: UUID!, $flowVersion: Int) {
  flowCanvas(flowId: $flowId, flowVersion: $flowVersion) {
    flow {
      id
      version
      name
      nodes { id targetId targetVersion alias executionSchedule }
    }
    layout {
      flowId
      flowVersion
      nodePositions { nodeReferenceId x y }
    }
    workBlockSummaries {
      id
      version
      name
      description
      executionHints
    }
  }
}
"""

FLOW_EXECUTION_CANVAS = """
query FlowExecutionCanvas($flowExecutionId: UUID!) {
  flowExecutionCanvas(flowExecutionId: $flowExecutionId) {
    flow {
      id
      version
      name
    }
    layout {
      flowId
    }
    execution {
      id
      flowId
      state
    }
      nodeStates {
        nodeReferenceId
        blockExecutionId
        state
        outcome { value metadata }
        executor { type identifier }
        latestEvent { id eventType }
      }
  }
}
"""


async def _create_work_block(name: str = "TestBlock") -> str:
    result = await schema.execute(
        CREATE_WORK_BLOCK,
        variable_values={
            "input": {
                "name": name,
                "description": f"Desc for {name}",
                "executionHints": ["manual"],
            }
        },
    )
    assert result.errors is None
    return result.data["createWorkBlock"]["id"]


async def _create_flow_with_nodes(
    wb_id: str, name: str = "Test Flow"
) -> tuple[str, list[str]]:
    """Create a flow with two nodes referencing the given work block.

    Returns (flow_id, [node_id_1, node_id_2]).
    """
    n1 = str(uuid.uuid4())
    n2 = str(uuid.uuid4())
    result = await schema.execute(
        CREATE_FLOW,
        variable_values={
            "input": {
                "name": name,
                "nodes": [
                    {
                        "id": n1,
                        "targetId": wb_id,
                        "targetVersion": 1,
                        "alias": "step1",
                        "executionSchedule": "cron: 0 9 * * 1-5",
                    },
                    {"id": n2, "targetId": wb_id, "targetVersion": 1, "alias": "step2"},
                ],
                "edges": [
                    {
                        "sourceId": n1,
                        "targetId": n2,
                        "portMappings": [{"sourcePort": "output", "targetPort": "input"}],
                    }
                ],
            }
        },
    )
    assert result.errors is None
    return result.data["createFlow"]["id"], [n1, n2]


# ── flow_canvas tests ─────────────────────────────────────────────


async def test_flow_canvas_returns_flow_and_summaries():
    wb_id = await _create_work_block("CanvasBlock")
    flow_id, _ = await _create_flow_with_nodes(wb_id, "Canvas Flow")

    result = await schema.execute(
        FLOW_CANVAS, variable_values={"flowId": flow_id}
    )
    assert result.errors is None
    data = result.data["flowCanvas"]

    assert data["flow"]["name"] == "Canvas Flow"
    assert len(data["flow"]["nodes"]) == 2
    assert data["flow"]["nodes"][0]["executionSchedule"] == "cron: 0 9 * * 1-5"

    summaries = data["workBlockSummaries"]
    assert len(summaries) >= 1
    assert summaries[0]["name"] == "CanvasBlock"
    assert summaries[0]["executionHints"] == ["manual"]


async def test_flow_canvas_specific_version():
    wb_id = await _create_work_block("VersionedBlock")
    flow_id, _ = await _create_flow_with_nodes(wb_id, "Version Flow")

    result = await schema.execute(
        FLOW_CANVAS, variable_values={"flowId": flow_id, "flowVersion": 1}
    )
    assert result.errors is None
    data = result.data["flowCanvas"]
    assert data["flow"]["version"] == 1


async def test_flow_canvas_nonexistent_returns_null():
    fake_id = str(uuid.uuid4())
    result = await schema.execute(
        FLOW_CANVAS, variable_values={"flowId": fake_id}
    )
    assert result.errors is None
    assert result.data["flowCanvas"] is None


async def test_flow_canvas_with_layout():
    wb_id = await _create_work_block("LayoutBlock")
    flow_id, node_ids = await _create_flow_with_nodes(wb_id, "Layout Flow")

    await CanvasLayoutDoc(
        flow_id=uuid.UUID(flow_id),
        flow_version=1,
        node_positions=[
            NodePositionDoc(
                node_reference_id=uuid.UUID(node_ids[0]), x=100.0, y=200.0
            ),
        ],
    ).insert()

    result = await schema.execute(
        FLOW_CANVAS, variable_values={"flowId": flow_id}
    )
    assert result.errors is None
    data = result.data["flowCanvas"]

    assert data["layout"] is not None
    assert data["layout"]["flowId"] == flow_id
    assert len(data["layout"]["nodePositions"]) == 1
    assert data["layout"]["nodePositions"][0]["x"] == 100.0


async def test_flow_canvas_no_layout_returns_null_layout():
    wb_id = await _create_work_block("NoLayout")
    flow_id, _ = await _create_flow_with_nodes(wb_id, "No Layout Flow")

    result = await schema.execute(
        FLOW_CANVAS, variable_values={"flowId": flow_id}
    )
    assert result.errors is None
    assert result.data["flowCanvas"]["layout"] is None


# ── flow_execution_canvas tests ──────────────────────────────────


async def test_flow_execution_canvas():
    wb_id_raw = await _create_work_block("ExecBlock")
    wb_id = uuid.UUID(wb_id_raw)
    flow_id, node_ids = await _create_flow_with_nodes(wb_id_raw, "Exec Flow")
    flow_uuid = uuid.UUID(flow_id)

    fe_id = uuid.uuid4()
    be_id = uuid.uuid4()

    await FlowExecutionDoc(
        execution_id=fe_id,
        flow_id=flow_uuid,
        flow_version=1,
        block_executions=[be_id],
        state="running",
    ).insert()

    await BlockExecutionDoc(
        execution_id=be_id,
        flow_execution_id=fe_id,
        node_reference_id=uuid.UUID(node_ids[0]),
        work_block_id=wb_id,
        work_block_version=1,
        outcome={"value": {"approved": True}, "metadata": {"source": "qa"}},
        state="assigned",
    ).insert()

    await ExecutionEventDoc(
        event_id=uuid.uuid4(),
        execution_id=be_id,
        event_type="assigned",
        executor=ExecutorInfoDoc(type="human", identifier="alice"),
    ).insert()

    result = await schema.execute(
        FLOW_EXECUTION_CANVAS,
        variable_values={"flowExecutionId": str(fe_id)},
    )
    assert result.errors is None
    data = result.data["flowExecutionCanvas"]

    assert data["flow"]["name"] == "Exec Flow"
    assert data["execution"]["state"] == "running"
    assert len(data["nodeStates"]) == 1

    ns = data["nodeStates"][0]
    assert ns["nodeReferenceId"] == node_ids[0]
    assert ns["state"] == "assigned"
    assert ns["outcome"]["value"] == {"approved": True}
    assert ns["outcome"]["metadata"]["source"] == "qa"
    assert ns["executor"]["type"] == "human"
    assert ns["executor"]["identifier"] == "alice"
    assert ns["latestEvent"]["eventType"] == "assigned"


async def test_flow_execution_canvas_nonexistent():
    result = await schema.execute(
        FLOW_EXECUTION_CANVAS,
        variable_values={"flowExecutionId": str(uuid.uuid4())},
    )
    assert result.errors is None
    assert result.data["flowExecutionCanvas"] is None


async def test_flow_execution_canvas_with_layout():
    wb_id_raw = await _create_work_block("ExecLayoutBlock")
    flow_id, node_ids = await _create_flow_with_nodes(wb_id_raw, "Exec Layout Flow")
    flow_uuid = uuid.UUID(flow_id)

    await CanvasLayoutDoc(
        flow_id=flow_uuid,
        flow_version=1,
        node_positions=[
            NodePositionDoc(
                node_reference_id=uuid.UUID(node_ids[0]), x=50.0, y=75.0
            ),
        ],
    ).insert()

    fe_id = uuid.uuid4()
    await FlowExecutionDoc(
        execution_id=fe_id,
        flow_id=flow_uuid,
        flow_version=1,
        block_executions=[],
        state="pending",
    ).insert()

    result = await schema.execute(
        FLOW_EXECUTION_CANVAS,
        variable_values={"flowExecutionId": str(fe_id)},
    )
    assert result.errors is None
    data = result.data["flowExecutionCanvas"]

    assert data["layout"] is not None
    assert data["layout"]["flowId"] == flow_id
    assert data["nodeStates"] == []
