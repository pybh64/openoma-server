"""Tests for GraphQL API endpoints."""

import pytest


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_check(self, test_client):
        response = await test_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestWorkBlockGraphQL:
    @pytest.mark.asyncio
    async def test_create_and_query_work_block(self, test_client):
        # Create
        create_mutation = """
        mutation {
            createWorkBlock(input: {
                name: "GraphQL Test Block"
                description: "Created via GraphQL"
                inputs: [{name: "in1", description: "input one"}]
                outputs: [{name: "out1", description: "output one"}]
                executionHints: ["api-gateway"]
            }) {
                id
                version
                name
                description
                inputs { name description required }
                outputs { name description }
                executionHints
            }
        }
        """
        response = await test_client.post(
            "/graphql", json={"query": create_mutation}
        )
        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"

        block = data["data"]["createWorkBlock"]
        assert block["name"] == "GraphQL Test Block"
        assert block["version"] == 1
        assert len(block["inputs"]) == 1
        assert block["inputs"][0]["name"] == "in1"
        assert block["executionHints"] == ["api-gateway"]

        block_id = block["id"]

        # Query
        query = f"""
        query {{
            workBlock(id: "{block_id}") {{
                id
                name
                version
            }}
        }}
        """
        response = await test_client.post("/graphql", json={"query": query})
        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"
        assert data["data"]["workBlock"]["name"] == "GraphQL Test Block"

    @pytest.mark.asyncio
    async def test_update_work_block(self, test_client):
        # Create
        create_resp = await test_client.post("/graphql", json={"query": """
        mutation {
            createWorkBlock(input: {name: "To Update"}) {
                id version
            }
        }
        """})
        block_id = create_resp.json()["data"]["createWorkBlock"]["id"]

        # Update
        update_resp = await test_client.post("/graphql", json={"query": f"""
        mutation {{
            updateWorkBlock(input: {{id: "{block_id}", name: "Updated Name"}}) {{
                id version name
            }}
        }}
        """})
        data = update_resp.json()
        assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"
        updated = data["data"]["updateWorkBlock"]
        assert updated["version"] == 2
        assert updated["name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_list_work_blocks(self, test_client):
        # Create two blocks
        for name in ["List A", "List B"]:
            await test_client.post("/graphql", json={"query": f"""
            mutation {{ createWorkBlock(input: {{name: "{name}"}}) {{ id }} }}
            """})

        # List
        response = await test_client.post("/graphql", json={"query": """
        query {
            workBlocks(latestOnly: false) {
                id name version
            }
        }
        """})
        data = response.json()
        assert "errors" not in data
        assert len(data["data"]["workBlocks"]) >= 2


class TestFlowGraphQL:
    @pytest.mark.asyncio
    async def test_create_flow(self, test_client):
        response = await test_client.post("/graphql", json={"query": """
        mutation {
            createFlow(input: {
                name: "Test Flow"
                description: "A test flow"
            }) {
                id version name description
            }
        }
        """})
        data = response.json()
        assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"
        flow = data["data"]["createFlow"]
        assert flow["name"] == "Test Flow"
        assert flow["version"] == 1


class TestContractGraphQL:
    @pytest.mark.asyncio
    async def test_create_contract(self, test_client):
        response = await test_client.post("/graphql", json={"query": """
        mutation {
            createContract(input: {
                name: "Test Contract"
                description: "A test contract"
            }) {
                id version name description
            }
        }
        """})
        data = response.json()
        assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"
        contract = data["data"]["createContract"]
        assert contract["name"] == "Test Contract"
        assert contract["version"] == 1
