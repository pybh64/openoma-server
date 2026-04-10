"""GraphQL integration tests using Strawberry's schema.execute."""

import pytest

from openoma_server.graphql.schema import schema

pytestmark = pytest.mark.asyncio

CREATE_WORK_BLOCK = """
mutation CreateWorkBlock($input: CreateWorkBlockInput!) {
  createWorkBlock(input: $input) {
    id
    version
    name
    description
    createdBy
    inputs { name description required }
    outputs { name }
    executionHints
    metadata
  }
}
"""

UPDATE_WORK_BLOCK = """
mutation UpdateWorkBlock($id: UUID!, $input: UpdateWorkBlockInput!) {
  updateWorkBlock(id: $id, input: $input) {
    id
    version
    name
    description
  }
}
"""

GET_WORK_BLOCK = """
query GetWorkBlock($id: UUID!, $version: Int) {
  workBlock(id: $id, version: $version) {
    id
    version
    name
  }
}
"""

LIST_WORK_BLOCKS = """
query ListWorkBlocks($name: String, $limit: Int) {
  workBlocks(name: $name, limit: $limit) {
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
    nodes {
      id
      targetId
      targetVersion
      alias
      metadata
    }
    edges {
      sourceId
      targetId
      condition { description }
      portMappings { sourcePort targetPort }
    }
  }
}
"""

CREATE_CONTRACT = """
mutation CreateContract($input: CreateContractInput!) {
  createContract(input: $input) {
    id
    version
    name
    owners { name role contact }
    workFlows { flowId flowVersion alias }
  }
}
"""

CREATE_REQUIRED_OUTCOME = """
mutation CreateRequiredOutcome($input: CreateRequiredOutcomeInput!) {
  createRequiredOutcome(input: $input) {
    id
    version
    name
    assessmentBindings {
      assessmentFlow { flowId flowVersion }
      testFlowRefs { flowId }
    }
  }
}
"""

HEALTH = """
query { health }
"""


async def test_health():
    result = await schema.execute(HEALTH)
    assert result.errors is None
    assert result.data["health"] == "ok"


async def test_create_work_block_graphql():
    result = await schema.execute(
        CREATE_WORK_BLOCK,
        variable_values={
            "input": {
                "name": "Review Document",
                "description": "Manual review step",
                "inputs": [
                    {"name": "document", "description": "The doc to review", "required": True}
                ],
                "outputs": [{"name": "approval", "required": True}],
                "executionHints": ["manual"],
                "metadata": {"color": "blue"},
            }
        },
    )
    assert result.errors is None
    data = result.data["createWorkBlock"]
    assert data["name"] == "Review Document"
    assert data["version"] == 1
    assert len(data["inputs"]) == 1
    assert data["inputs"][0]["name"] == "document"
    assert data["executionHints"] == ["manual"]
    assert data["metadata"]["color"] == "blue"


async def test_update_work_block_graphql():
    # Create first
    create_result = await schema.execute(
        CREATE_WORK_BLOCK,
        variable_values={"input": {"name": "Original"}},
    )
    wb_id = create_result.data["createWorkBlock"]["id"]

    # Update
    result = await schema.execute(
        UPDATE_WORK_BLOCK,
        variable_values={
            "id": wb_id,
            "input": {"name": "Updated", "description": "New desc"},
        },
    )
    assert result.errors is None
    data = result.data["updateWorkBlock"]
    assert data["version"] == 2
    assert data["name"] == "Updated"


async def test_get_work_block_graphql():
    create_result = await schema.execute(
        CREATE_WORK_BLOCK,
        variable_values={"input": {"name": "Fetchable"}},
    )
    wb_id = create_result.data["createWorkBlock"]["id"]

    result = await schema.execute(
        GET_WORK_BLOCK,
        variable_values={"id": wb_id},
    )
    assert result.errors is None
    assert result.data["workBlock"]["name"] == "Fetchable"


async def test_get_work_block_specific_version():
    create_result = await schema.execute(
        CREATE_WORK_BLOCK,
        variable_values={"input": {"name": "V1"}},
    )
    wb_id = create_result.data["createWorkBlock"]["id"]

    await schema.execute(
        UPDATE_WORK_BLOCK,
        variable_values={"id": wb_id, "input": {"name": "V2"}},
    )

    result = await schema.execute(
        GET_WORK_BLOCK,
        variable_values={"id": wb_id, "version": 1},
    )
    assert result.data["workBlock"]["name"] == "V1"
    assert result.data["workBlock"]["version"] == 1


async def test_list_work_blocks_graphql():
    await schema.execute(
        CREATE_WORK_BLOCK,
        variable_values={"input": {"name": "GQL_List_A"}},
    )
    await schema.execute(
        CREATE_WORK_BLOCK,
        variable_values={"input": {"name": "GQL_List_B"}},
    )

    result = await schema.execute(
        LIST_WORK_BLOCKS,
        variable_values={"name": "GQL_List", "limit": 10},
    )
    assert result.errors is None
    assert len(result.data["workBlocks"]) >= 2


async def test_create_flow_graphql():
    # Create a work block to reference
    wb_result = await schema.execute(
        CREATE_WORK_BLOCK,
        variable_values={"input": {"name": "Flow Step"}},
    )
    wb_id = wb_result.data["createWorkBlock"]["id"]

    import uuid

    n1 = str(uuid.uuid4())
    n2 = str(uuid.uuid4())

    result = await schema.execute(
        CREATE_FLOW,
        variable_values={
            "input": {
                "name": "Test Flow",
                "nodes": [
                    {
                        "id": n1,
                        "targetId": wb_id,
                        "targetVersion": 1,
                        "alias": "step1",
                        "metadata": {"position": {"x": 0, "y": 0}},
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
    data = result.data["createFlow"]
    assert data["name"] == "Test Flow"
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1
    assert data["nodes"][0]["metadata"]["position"] == {"x": 0, "y": 0}


async def test_create_contract_graphql():
    import uuid

    flow_id = str(uuid.uuid4())

    result = await schema.execute(
        CREATE_CONTRACT,
        variable_values={
            "input": {
                "name": "Test Contract",
                "owners": [
                    {"name": "Alice", "role": "lead", "contact": "alice@test.com"},
                    {"name": "Bob", "role": "reviewer"},
                ],
                "workFlows": [{"flowId": flow_id, "flowVersion": 1, "alias": "main"}],
            }
        },
    )
    assert result.errors is None
    data = result.data["createContract"]
    assert data["name"] == "Test Contract"
    assert len(data["owners"]) == 2
    assert data["owners"][0]["name"] == "Alice"
    assert data["workFlows"][0]["alias"] == "main"


async def test_create_required_outcome_graphql():
    import uuid

    flow_id = str(uuid.uuid4())

    result = await schema.execute(
        CREATE_REQUIRED_OUTCOME,
        variable_values={
            "input": {
                "name": "Quality Gate",
                "assessmentBindings": [
                    {
                        "assessmentFlow": {"flowId": flow_id, "flowVersion": 1},
                        "testFlowRefs": [{"flowId": str(uuid.uuid4()), "flowVersion": 1}],
                    }
                ],
            }
        },
    )
    assert result.errors is None
    data = result.data["createRequiredOutcome"]
    assert data["name"] == "Quality Gate"
    assert len(data["assessmentBindings"]) == 1


async def test_get_nonexistent_returns_null():
    import uuid

    result = await schema.execute(
        GET_WORK_BLOCK,
        variable_values={"id": str(uuid.uuid4())},
    )
    assert result.errors is None
    assert result.data["workBlock"] is None
