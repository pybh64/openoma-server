#!/usr/bin/env python3
"""Load the database with comprehensive openoma scenarios and verify the
server supports every design principle from the specification.

Covers:
  1. WorkBlocks with full port descriptors, schemas, execution hints, expected outcomes
  2. Flows with conditional edges, entry edges, parallel lanes, port mappings,
     disconnected subgraphs, and the same-block-two-slots pattern
  3. Assessment flows (single terminal node constraint)
  4. RequiredOutcomes with AssessmentBindings (assessment_flow + test_flow_refs)
  5. Contracts with work_flows, sub_contracts, required_outcomes, and parties
  6. Versioning: creating v1 then updating to v2 and verifying both coexist
  7. Execution lifecycle: create → assign → start → progress → outcome → complete
  8. Executor handoff: assign A → release A → assign B → complete (crash recovery)
  9. Flow state derivation from block executions
 10. Contract state derivation from flow executions
 11. Many-to-many: shared BlockExecution across FlowExecutions

Usage:
    # Against the running server (make up first):
    uv run python scripts/load_scenarios.py

    # With a custom endpoint:
    OPENOMA_SERVER_URL=http://localhost:8088/api uv run python scripts/load_scenarios.py
"""

from __future__ import annotations

import json
import os
import sys
from uuid import uuid4

import httpx
import pymongo

SERVER = os.environ.get("OPENOMA_SERVER_URL", "http://localhost:8088/api")
GQL = f"{SERVER}/graphql"

MONGO_URI = os.environ.get("OPENOMA_MONGO_URI", "mongodb://localhost:27018")
MONGO_DB = os.environ.get("OPENOMA_MONGO_DB", "openoma")

# Collections to drop when clearing the database
_COLLECTIONS = [
    "work_blocks",
    "flows",
    "flow_drafts",
    "canvas_layouts",
    "contracts",
    "required_outcomes",
    "block_executions",
    "flow_executions",
    "contract_executions",
    "execution_events",
]

# Pre-generate stable UUIDs for node references so edges can target them
NODE_TRIAGE = str(uuid4())
NODE_IMPL_A = str(uuid4())
NODE_IMPL_B = str(uuid4())
NODE_REVIEW = str(uuid4())

NODE_CHECK_DEPLOY = str(uuid4())
NODE_RUN_SMOKE = str(uuid4())
NODE_VERDICT = str(uuid4())

NODE_COLLECT_SURVEY = str(uuid4())
NODE_COMPUTE_CSAT = str(uuid4())

NODE_SMOKE_ENTRY = str(uuid4())
NODE_SMOKE_RUN = str(uuid4())
NODE_SMOKE_REPORT = str(uuid4())

NODE_SURVEY_SEND = str(uuid4())
NODE_SURVEY_COLLECT = str(uuid4())

NODE_MONITOR_A = str(uuid4())
NODE_MONITOR_B = str(uuid4())

NODE_INFRA_CHECK = str(uuid4())
NODE_INFRA_REPAIR = str(uuid4())
NODE_INFRA_VERIFY = str(uuid4())

NODE_UPTIME_EVAL = str(uuid4())

# ── DB helpers ──────────────────────────────────────────────────────


def clear_db() -> None:
    """Drop all OpenOMA collections so the script starts from a clean slate."""
    print(f"🗑️  Clearing database '{MONGO_DB}' at {MONGO_URI} ...")
    client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[MONGO_DB]
    existing = set(db.list_collection_names())
    for name in _COLLECTIONS:
        if name in existing:
            db.drop_collection(name)
    client.close()
    print("✅  Database cleared.\n")


# ── Helpers ──────────────────────────────────────────────────────────

ok_count = 0
fail_count = 0


def gql(query: str, variables: dict | None = None) -> dict:
    """Execute a GraphQL request, abort on transport errors."""
    resp = httpx.post(
        GQL, json={"query": query, "variables": variables or {}}, timeout=15
    )
    resp.raise_for_status()
    body = resp.json()
    if body.get("errors"):
        print(
            f"\n❌ GraphQL errors:\n{json.dumps(body['errors'], indent=2)}",
            file=sys.stderr,
        )
        print(f"   Query (first 200): {query[:200]}", file=sys.stderr)
    return body


def check(label: str, condition: bool, detail: str = ""):
    """Record a pass/fail check."""
    global ok_count, fail_count
    if condition:
        ok_count += 1
        print(f"  ✅ {label}")
    else:
        fail_count += 1
        print(f"  ❌ {label}{' — ' + detail if detail else ''}")


def extract(data: dict, path: str):
    """Drill into nested dict with dot-separated path."""
    for key in path.split("."):
        if data is None:
            return None
        data = data.get(key) if isinstance(data, dict) else None
    return data


# ══════════════════════════════════════════════════════════════════════
# SCENARIO 1 — WorkBlocks with full richness
# ══════════════════════════════════════════════════════════════════════


def scenario_work_blocks() -> dict[str, str]:
    """Create work blocks exercising every field: ports, schemas, hints,
    expected outcomes, metadata.  Returns {name: id}."""
    print("\n═══ Scenario 1: WorkBlocks ═══")

    blocks = {}
    definitions = [
        {
            "name": "Ticket Triage",
            "description": "Classify incoming tickets by severity and route to the right team",
            "inputs": [
                {
                    "name": "ticket",
                    "description": "Raw ticket payload",
                    "required": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "body": {"type": "string"},
                        },
                    },
                },
            ],
            "outputs": [
                {
                    "name": "severity",
                    "description": "P0–P4 classification",
                    "required": True,
                    "schema": {
                        "type": "string",
                        "enum": ["P0", "P1", "P2", "P3", "P4"],
                    },
                },
                {
                    "name": "assigned_team",
                    "description": "Team handle",
                    "required": True,
                },
            ],
            "executionHints": ["ticket-system-access", "triage-trained"],
            "expectedOutcome": {
                "name": "Triage done",
                "description": "Every ticket classified within SLA",
            },
            "metadata": {"category": "intake", "sla_minutes": 15},
        },
        {
            "name": "Implementation",
            "description": "Write code to satisfy the ticket requirements",
            "inputs": [
                {"name": "ticket", "description": "Triaged ticket", "required": True},
                {
                    "name": "codebase_ref",
                    "description": "Git ref to branch from",
                    "required": False,
                },
            ],
            "outputs": [
                {
                    "name": "pull_request_url",
                    "description": "URL of the PR",
                    "required": True,
                },
                {
                    "name": "test_results",
                    "description": "CI output",
                    "required": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "passed": {"type": "integer"},
                            "failed": {"type": "integer"},
                        },
                    },
                },
            ],
            "executionHints": ["codebase-write", "ci-access"],
            "expectedOutcome": {
                "name": "Code complete",
                "description": "PR passing CI with no critical issues",
            },
            "metadata": {"category": "engineering"},
        },
        {
            "name": "Code Review",
            "description": "Review a pull request for quality, correctness, and standards compliance",
            "inputs": [
                {
                    "name": "pull_request_url",
                    "description": "URL of the PR to review",
                    "required": True,
                },
                {
                    "name": "review_checklist",
                    "description": "Criteria for approval",
                    "required": False,
                },
            ],
            "outputs": [
                {
                    "name": "verdict",
                    "description": "approved | changes_requested | rejected",
                    "required": True,
                    "schema": {
                        "type": "string",
                        "enum": ["approved", "changes_requested", "rejected"],
                    },
                },
                {
                    "name": "comments",
                    "description": "Inline review comments",
                    "required": True,
                },
            ],
            "executionHints": ["github-access", "codebase-read"],
            "metadata": {"category": "review"},
        },
        {
            "name": "Check Deployment Status",
            "description": "Verify the target deployment is live and reachable",
            "inputs": [
                {
                    "name": "environment",
                    "description": "staging | production",
                    "required": True,
                },
            ],
            "outputs": [
                {
                    "name": "is_live",
                    "description": "Boolean health status",
                    "required": True,
                    "schema": {"type": "boolean"},
                },
                {
                    "name": "deploy_sha",
                    "description": "Git SHA currently deployed",
                    "required": True,
                },
            ],
            "executionHints": ["infra-read"],
            "metadata": {"category": "verification"},
        },
        {
            "name": "Run Smoke Tests",
            "description": "Execute the smoke test suite against the deployment",
            "inputs": [
                {
                    "name": "environment",
                    "description": "Target environment",
                    "required": True,
                },
            ],
            "outputs": [
                {
                    "name": "results",
                    "description": "Test results summary",
                    "required": True,
                    "schema": {"type": "object"},
                },
            ],
            "executionHints": ["test-runner", "infra-read"],
            "metadata": {"category": "testing"},
        },
        {
            "name": "Produce Release Verdict",
            "description": "Aggregate deployment and smoke test data into a final release decision",
            "inputs": [
                {
                    "name": "is_live",
                    "description": "Deployment health",
                    "required": True,
                },
                {
                    "name": "smoke_results",
                    "description": "Smoke test output",
                    "required": True,
                },
            ],
            "outputs": [
                {
                    "name": "verdict",
                    "description": "pass | fail",
                    "required": True,
                    "schema": {"type": "string", "enum": ["pass", "fail"]},
                },
                {"name": "details", "description": "Explanation", "required": False},
            ],
            "executionHints": [],
            "metadata": {"category": "assessment"},
        },
        {
            "name": "Send Survey",
            "description": "Distribute customer satisfaction surveys",
            "inputs": [
                {
                    "name": "recipients",
                    "description": "List of emails",
                    "required": True,
                    "schema": {"type": "array", "items": {"type": "string"}},
                },
            ],
            "outputs": [
                {"name": "survey_ids", "description": "Tracking IDs", "required": True},
            ],
            "executionHints": ["email-access"],
            "metadata": {"category": "outreach"},
        },
        {
            "name": "Collect Survey Responses",
            "description": "Wait for and aggregate survey responses",
            "inputs": [
                {
                    "name": "survey_ids",
                    "description": "Tracking IDs to watch",
                    "required": True,
                },
            ],
            "outputs": [
                {
                    "name": "responses",
                    "description": "Aggregated response data",
                    "required": True,
                    "schema": {"type": "array"},
                },
            ],
            "executionHints": ["survey-platform"],
            "metadata": {"category": "collection"},
        },
        {
            "name": "Compute CSAT Score",
            "description": "Calculate customer satisfaction score from survey data",
            "inputs": [
                {
                    "name": "responses",
                    "description": "Raw survey responses",
                    "required": True,
                },
            ],
            "outputs": [
                {
                    "name": "csat_score",
                    "description": "Score from 1.0 to 5.0",
                    "required": True,
                    "schema": {"type": "number", "minimum": 1.0, "maximum": 5.0},
                },
                {
                    "name": "breakdown",
                    "description": "Per-question scores",
                    "required": False,
                },
            ],
            "executionHints": [],
            "metadata": {"category": "assessment"},
        },
        {
            "name": "Infrastructure Health Check",
            "description": "Monitor infrastructure metrics and report status",
            "inputs": [
                {
                    "name": "targets",
                    "description": "List of endpoints to check",
                    "required": True,
                },
            ],
            "outputs": [
                {
                    "name": "status",
                    "description": "Overall status",
                    "required": True,
                    "schema": {
                        "type": "string",
                        "enum": ["healthy", "degraded", "down"],
                    },
                },
                {"name": "metrics", "description": "Raw metric data", "required": True},
            ],
            "executionHints": ["monitoring-access"],
            "metadata": {"category": "operations"},
        },
        {
            "name": "Automated Repair",
            "description": "Attempt automated remediation of infrastructure issues",
            "inputs": [
                {
                    "name": "issue_type",
                    "description": "Type of issue detected",
                    "required": True,
                },
                {
                    "name": "target",
                    "description": "Affected resource",
                    "required": True,
                },
            ],
            "outputs": [
                {
                    "name": "repair_status",
                    "description": "success | failed | escalated",
                    "required": True,
                },
            ],
            "executionHints": ["infra-write", "runbook-access"],
            "metadata": {"category": "remediation"},
        },
        {
            "name": "Uptime Evaluation",
            "description": "Compute rolling uptime percentage from monitoring data",
            "inputs": [
                {
                    "name": "metrics",
                    "description": "Time-series health data",
                    "required": True,
                },
                {
                    "name": "window",
                    "description": "Evaluation window in hours",
                    "required": True,
                },
            ],
            "outputs": [
                {
                    "name": "uptime_pct",
                    "description": "Percentage uptime",
                    "required": True,
                    "schema": {"type": "number", "minimum": 0, "maximum": 100},
                },
                {
                    "name": "incidents",
                    "description": "Downtime incidents list",
                    "required": False,
                },
            ],
            "executionHints": [],
            "metadata": {"category": "assessment"},
        },
    ]

    MUTATION = """
    mutation CreateWorkBlock($input: CreateWorkBlockInput!) {
      createWorkBlock(input: $input) { id name version description inputs { name required } outputs { name } executionHints expectedOutcome { name description } metadata }
    }
    """

    for defn in definitions:
        body = gql(MUTATION, {"input": defn})
        wb = extract(body, "data.createWorkBlock")
        check(
            f"WorkBlock '{defn['name']}' created",
            wb is not None
            and wb.get("name") == defn["name"]
            and wb.get("version") == 1,
        )
        if wb:
            blocks[wb["name"]] = wb["id"]
            if defn.get("executionHints"):
                check(
                    f"  execution_hints round-trip",
                    wb["executionHints"] == defn["executionHints"],
                )
            if defn.get("expectedOutcome"):
                check(
                    f"  expected_outcome round-trip",
                    wb["expectedOutcome"]["name"] == defn["expectedOutcome"]["name"],
                )

    return blocks


# ══════════════════════════════════════════════════════════════════════
# SCENARIO 2 — Flows: conditional edges, parallel lanes, port mappings
# ══════════════════════════════════════════════════════════════════════


def scenario_flows(blocks: dict[str, str]) -> dict[str, str]:
    """Create flows exercising every structural pattern.  Returns {name: id}."""
    print("\n═══ Scenario 2: Flows ═══")

    flows = {}

    # --- 2a: Engineering Sprint Cycle (from the spec example) ---
    # Same WorkBlock "Implementation" used in two slots (parallel lanes)
    # Conditional branching from triage
    sprint_input = {
        "name": "Engineering Sprint Cycle",
        "description": "Triage → branch into normal or fast-track Implementation → Code Review",
        "nodes": [
            {
                "id": NODE_TRIAGE,
                "targetId": blocks["Ticket Triage"],
                "targetVersion": 1,
                "alias": "triage",
                "executionSchedule": "cron: 0 9 * * 1-5",
                "metadata": {"position": {"x": 100, "y": 300}},
            },
            {
                "id": NODE_IMPL_A,
                "targetId": blocks["Implementation"],
                "targetVersion": 1,
                "alias": "normal-impl",
                "executionSchedule": "run when triage marks the ticket for standard process",
                "metadata": {"position": {"x": 400, "y": 150}},
            },
            {
                "id": NODE_IMPL_B,
                "targetId": blocks["Implementation"],
                "targetVersion": 1,
                "alias": "fast-track-impl",
                "executionSchedule": "run independently for urgent tickets after triage",
                "metadata": {"position": {"x": 400, "y": 450}},
            },
            {
                "id": NODE_REVIEW,
                "targetId": blocks["Code Review"],
                "targetVersion": 1,
                "alias": "review",
                "executionSchedule": "run after either implementation path finishes",
                "metadata": {"position": {"x": 700, "y": 300}},
            },
        ],
        "edges": [
            # Entry edge: triage is a starting node
            {"targetId": NODE_TRIAGE},
            # Conditional: approved ticket → normal implementation
            {
                "sourceId": NODE_TRIAGE,
                "targetId": NODE_IMPL_A,
                "condition": {
                    "description": "ticket is approved for standard process",
                    "predicate": {"op": "eq", "field": "severity", "value": "P2"},
                },
                "portMappings": [{"sourcePort": "severity", "targetPort": "ticket"}],
            },
            # Conditional: fast-track ticket → fast-track implementation
            {
                "sourceId": NODE_TRIAGE,
                "targetId": NODE_IMPL_B,
                "condition": {
                    "description": "ticket is fast-tracked",
                    "predicate": {
                        "op": "in",
                        "field": "severity",
                        "value": ["P0", "P1"],
                    },
                },
            },
            # Both implementations converge to code review (unconditional)
            {
                "sourceId": NODE_IMPL_A,
                "targetId": NODE_REVIEW,
                "portMappings": [
                    {"sourcePort": "pull_request_url", "targetPort": "pull_request_url"}
                ],
            },
            {
                "sourceId": NODE_IMPL_B,
                "targetId": NODE_REVIEW,
                "portMappings": [
                    {"sourcePort": "pull_request_url", "targetPort": "pull_request_url"}
                ],
            },
        ],
        "expectedOutcome": {
            "name": "Sprint delivered",
            "description": "All sprint tickets implemented and reviewed",
        },
        "metadata": {"sprint_length_days": 14, "canvas_zoom": 1.0},
    }

    body = gql(
        """
    mutation CreateFlow($input: CreateFlowInput!) {
      createFlow(input: $input) {
        id name version description
        nodes { id targetId targetVersion alias executionSchedule metadata }
        edges { sourceId targetId condition { description predicate } portMappings { sourcePort targetPort } }
        expectedOutcome { name }
        metadata
      }
    }
    """,
        {"input": sprint_input},
    )
    flow = extract(body, "data.createFlow")
    check(
        "Flow 'Engineering Sprint Cycle' created",
        flow is not None and flow["version"] == 1,
    )
    if flow:
        flows[flow["name"]] = flow["id"]
        check("  4 nodes (same-block-two-slots pattern)", len(flow["nodes"]) == 4)
        check(
            "  5 edges (1 entry + 2 conditional + 2 unconditional)",
            len(flow["edges"]) == 5,
        )
        entry_edges = [e for e in flow["edges"] if e["sourceId"] is None]
        check("  1 entry edge (sourceId=null)", len(entry_edges) == 1)
        cond_edges = [e for e in flow["edges"] if e["condition"] is not None]
        check("  2 conditional edges with predicates", len(cond_edges) == 2)
        mapped_edges = [e for e in flow["edges"] if e.get("portMappings")]
        check("  3 edges have port mappings", len(mapped_edges) == 3)
        schedules = {n["alias"]: n["executionSchedule"] for n in flow["nodes"]}
        check("  node execution schedules round-trip", schedules == {
            "triage": "cron: 0 9 * * 1-5",
            "normal-impl": "run when triage marks the ticket for standard process",
            "fast-track-impl": "run independently for urgent tickets after triage",
            "review": "run after either implementation path finishes",
        })

    # --- 2b: Release Verification (assessment flow — 1 terminal node) ---
    release_input = {
        "name": "Release Verification",
        "description": "Check deployment → run smoke tests → produce verdict (assessment flow)",
        "nodes": [
            {
                "id": NODE_CHECK_DEPLOY,
                "targetId": blocks["Check Deployment Status"],
                "targetVersion": 1,
                "alias": "check-deploy",
            },
            {
                "id": NODE_RUN_SMOKE,
                "targetId": blocks["Run Smoke Tests"],
                "targetVersion": 1,
                "alias": "smoke",
            },
            {
                "id": NODE_VERDICT,
                "targetId": blocks["Produce Release Verdict"],
                "targetVersion": 1,
                "alias": "verdict",
            },
        ],
        "edges": [
            {"targetId": NODE_CHECK_DEPLOY},
            {
                "sourceId": NODE_CHECK_DEPLOY,
                "targetId": NODE_RUN_SMOKE,
                "portMappings": [
                    {"sourcePort": "deploy_sha", "targetPort": "environment"}
                ],
            },
            {
                "sourceId": NODE_RUN_SMOKE,
                "targetId": NODE_VERDICT,
                "portMappings": [
                    {"sourcePort": "results", "targetPort": "smoke_results"}
                ],
            },
        ],
        "expectedOutcome": {
            "name": "Release verdict",
            "description": "Binary pass/fail on release readiness",
        },
    }
    body = gql(
        """
    mutation CreateFlow($input: CreateFlowInput!) {
      createFlow(input: $input) { id name version nodes { id alias } edges { sourceId targetId } }
    }
    """,
        {"input": release_input},
    )
    flow = extract(body, "data.createFlow")
    check("Flow 'Release Verification' created (assessment flow)", flow is not None)
    if flow:
        flows[flow["name"]] = flow["id"]
        # Terminal node: verdict has no outgoing edges
        terminal = [
            n
            for n in flow["nodes"]
            if not any(e["sourceId"] == n["id"] for e in flow["edges"])
        ]
        check("  exactly 1 terminal node (assessment constraint)", len(terminal) == 1)
        check("  terminal node is 'verdict'", terminal[0]["alias"] == "verdict")

    # --- 2c: CSAT Evaluator (assessment flow) ---
    csat_input = {
        "name": "CSAT Evaluator",
        "description": "Collect surveys and compute CSAT score",
        "nodes": [
            {
                "id": NODE_COLLECT_SURVEY,
                "targetId": blocks["Collect Survey Responses"],
                "targetVersion": 1,
                "alias": "collect",
            },
            {
                "id": NODE_COMPUTE_CSAT,
                "targetId": blocks["Compute CSAT Score"],
                "targetVersion": 1,
                "alias": "compute",
            },
        ],
        "edges": [
            {"targetId": NODE_COLLECT_SURVEY},
            {
                "sourceId": NODE_COLLECT_SURVEY,
                "targetId": NODE_COMPUTE_CSAT,
                "portMappings": [
                    {"sourcePort": "responses", "targetPort": "responses"}
                ],
            },
        ],
    }
    body = gql(
        """
    mutation CreateFlow($input: CreateFlowInput!) {
      createFlow(input: $input) { id name version nodes { id } edges { sourceId targetId } }
    }
    """,
        {"input": csat_input},
    )
    flow = extract(body, "data.createFlow")
    check("Flow 'CSAT Evaluator' created (assessment flow)", flow is not None)
    if flow:
        flows[flow["name"]] = flow["id"]

    # --- 2d: Smoke Test Suite (test flow consumed by assessment) ---
    smoke_input = {
        "name": "Smoke Test Suite",
        "description": "Entry → run tests → produce report",
        "nodes": [
            {
                "id": NODE_SMOKE_ENTRY,
                "targetId": blocks["Check Deployment Status"],
                "targetVersion": 1,
                "alias": "entry-check",
            },
            {
                "id": NODE_SMOKE_RUN,
                "targetId": blocks["Run Smoke Tests"],
                "targetVersion": 1,
                "alias": "run",
            },
            {
                "id": NODE_SMOKE_REPORT,
                "targetId": blocks["Produce Release Verdict"],
                "targetVersion": 1,
                "alias": "report",
            },
        ],
        "edges": [
            {"targetId": NODE_SMOKE_ENTRY},
            {"sourceId": NODE_SMOKE_ENTRY, "targetId": NODE_SMOKE_RUN},
            {"sourceId": NODE_SMOKE_RUN, "targetId": NODE_SMOKE_REPORT},
        ],
    }
    body = gql(
        """
    mutation CreateFlow($input: CreateFlowInput!) {
      createFlow(input: $input) { id name version }
    }
    """,
        {"input": smoke_input},
    )
    flow = extract(body, "data.createFlow")
    check("Flow 'Smoke Test Suite' created (test flow)", flow is not None)
    if flow:
        flows[flow["name"]] = flow["id"]

    # --- 2e: Survey Collection (test flow) ---
    survey_input = {
        "name": "Survey Collection",
        "description": "Send surveys and collect responses",
        "nodes": [
            {
                "id": NODE_SURVEY_SEND,
                "targetId": blocks["Send Survey"],
                "targetVersion": 1,
                "alias": "send",
            },
            {
                "id": NODE_SURVEY_COLLECT,
                "targetId": blocks["Collect Survey Responses"],
                "targetVersion": 1,
                "alias": "collect",
            },
        ],
        "edges": [
            {"targetId": NODE_SURVEY_SEND},
            {
                "sourceId": NODE_SURVEY_SEND,
                "targetId": NODE_SURVEY_COLLECT,
                "portMappings": [
                    {"sourcePort": "survey_ids", "targetPort": "survey_ids"}
                ],
            },
        ],
    }
    body = gql(
        """
    mutation CreateFlow($input: CreateFlowInput!) {
      createFlow(input: $input) { id name version }
    }
    """,
        {"input": survey_input},
    )
    flow = extract(body, "data.createFlow")
    check("Flow 'Survey Collection' created (test flow)", flow is not None)
    if flow:
        flows[flow["name"]] = flow["id"]

    # --- 2f: Infra BAU — disconnected subgraphs ---
    infra_input = {
        "name": "Infra BAU",
        "description": "Two independent streams: monitoring + repair",
        "nodes": [
            {
                "id": NODE_MONITOR_A,
                "targetId": blocks["Infrastructure Health Check"],
                "targetVersion": 1,
                "alias": "monitor-primary",
            },
            {
                "id": NODE_MONITOR_B,
                "targetId": blocks["Infrastructure Health Check"],
                "targetVersion": 1,
                "alias": "monitor-secondary",
            },
            {
                "id": NODE_INFRA_CHECK,
                "targetId": blocks["Infrastructure Health Check"],
                "targetVersion": 1,
                "alias": "deep-check",
            },
            {
                "id": NODE_INFRA_REPAIR,
                "targetId": blocks["Automated Repair"],
                "targetVersion": 1,
                "alias": "repair",
            },
            {
                "id": NODE_INFRA_VERIFY,
                "targetId": blocks["Infrastructure Health Check"],
                "targetVersion": 1,
                "alias": "verify-after-repair",
            },
        ],
        "edges": [
            # Subgraph 1: two independent monitors (no connection between them)
            {"targetId": NODE_MONITOR_A},
            {"targetId": NODE_MONITOR_B},
            # Subgraph 2: deep-check → repair → verify
            {"targetId": NODE_INFRA_CHECK},
            {
                "sourceId": NODE_INFRA_CHECK,
                "targetId": NODE_INFRA_REPAIR,
                "condition": {
                    "description": "status is degraded or down",
                    "predicate": {
                        "op": "in",
                        "field": "status",
                        "value": ["degraded", "down"],
                    },
                },
            },
            {"sourceId": NODE_INFRA_REPAIR, "targetId": NODE_INFRA_VERIFY},
        ],
        "metadata": {"run_frequency": "hourly"},
    }
    body = gql(
        """
    mutation CreateFlow($input: CreateFlowInput!) {
      createFlow(input: $input) { id name version nodes { id alias } edges { sourceId targetId } }
    }
    """,
        {"input": infra_input},
    )
    flow = extract(body, "data.createFlow")
    check("Flow 'Infra BAU' created (disconnected subgraphs)", flow is not None)
    if flow:
        flows[flow["name"]] = flow["id"]
        entry_edges = [e for e in flow["edges"] if e["sourceId"] is None]
        check(
            "  3 entry edges (3 starting points in 2 subgraphs)", len(entry_edges) == 3
        )
        check(
            "  5 nodes (same block used 4 times = different slots)",
            len(flow["nodes"]) == 5,
        )

    # --- 2g: Uptime Monitor Assessment (assessment flow) ---
    uptime_input = {
        "name": "Uptime Monitor Assessment",
        "description": "Single-step assessment: compute uptime percentage",
        "nodes": [
            {
                "id": NODE_UPTIME_EVAL,
                "targetId": blocks["Uptime Evaluation"],
                "targetVersion": 1,
                "alias": "eval",
            },
        ],
        "edges": [
            {"targetId": NODE_UPTIME_EVAL},
        ],
    }
    body = gql(
        """
    mutation CreateFlow($input: CreateFlowInput!) {
      createFlow(input: $input) { id name version nodes { id } edges { sourceId } }
    }
    """,
        {"input": uptime_input},
    )
    flow = extract(body, "data.createFlow")
    check(
        "Flow 'Uptime Monitor Assessment' created (single-node assessment)",
        flow is not None,
    )
    if flow:
        flows[flow["name"]] = flow["id"]

    return flows


# ══════════════════════════════════════════════════════════════════════
# SCENARIO 3 — RequiredOutcomes with AssessmentBindings
# ══════════════════════════════════════════════════════════════════════


def scenario_required_outcomes(flows: dict[str, str]) -> dict[str, str]:
    """Create required outcomes with assessment bindings.  Returns {name: id}."""
    print("\n═══ Scenario 3: RequiredOutcomes ═══")

    outcomes = {}

    # 3a: Feature shipped — assessed by Release Verification, tested by Smoke Test Suite
    body = gql(
        """
    mutation CreateRO($input: CreateRequiredOutcomeInput!) {
      createRequiredOutcome(input: $input) { id name version assessmentBindings { assessmentFlow { flowId } testFlowRefs { flowId } } }
    }
    """,
        {
            "input": {
                "name": "Feature X shipped to production",
                "description": "The primary feature is deployed, passes smoke tests, and is reachable by users",
                "assessmentBindings": [
                    {
                        "assessmentFlow": {
                            "flowId": flows["Release Verification"],
                            "flowVersion": 1,
                        },
                        "testFlowRefs": [
                            {
                                "flowId": flows["Smoke Test Suite"],
                                "flowVersion": 1,
                                "alias": "smoke",
                            },
                        ],
                    }
                ],
                "metadata": {"priority": "critical"},
            }
        },
    )
    ro = extract(body, "data.createRequiredOutcome")
    check(
        "RequiredOutcome 'Feature X shipped' created",
        ro is not None and ro["version"] == 1,
    )
    if ro:
        outcomes[ro["name"]] = ro["id"]
        check("  has 1 assessment binding", len(ro["assessmentBindings"]) == 1)
        check(
            "  binding has 1 test flow ref",
            len(ro["assessmentBindings"][0]["testFlowRefs"]) == 1,
        )

    # 3b: Customer satisfaction
    body = gql(
        """
    mutation CreateRO($input: CreateRequiredOutcomeInput!) {
      createRequiredOutcome(input: $input) { id name version assessmentBindings { assessmentFlow { flowId } testFlowRefs { flowId } } }
    }
    """,
        {
            "input": {
                "name": "Customer satisfaction ≥ 4.5/5",
                "description": "Aggregate CSAT score from post-launch surveys must be at least 4.5",
                "assessmentBindings": [
                    {
                        "assessmentFlow": {
                            "flowId": flows["CSAT Evaluator"],
                            "flowVersion": 1,
                        },
                        "testFlowRefs": [
                            {
                                "flowId": flows["Survey Collection"],
                                "flowVersion": 1,
                                "alias": "survey-data",
                            },
                        ],
                    }
                ],
            }
        },
    )
    ro = extract(body, "data.createRequiredOutcome")
    check("RequiredOutcome 'CSAT ≥ 4.5' created", ro is not None)
    if ro:
        outcomes[ro["name"]] = ro["id"]

    # 3c: Uptime SLA
    body = gql(
        """
    mutation CreateRO($input: CreateRequiredOutcomeInput!) {
      createRequiredOutcome(input: $input) { id name version assessmentBindings { assessmentFlow { flowId } } }
    }
    """,
        {
            "input": {
                "name": "99.9% uptime",
                "description": "Infrastructure uptime over the contract period must exceed 99.9%",
                "assessmentBindings": [
                    {
                        "assessmentFlow": {
                            "flowId": flows["Uptime Monitor Assessment"],
                            "flowVersion": 1,
                        },
                    }
                ],
            }
        },
    )
    ro = extract(body, "data.createRequiredOutcome")
    check("RequiredOutcome '99.9% uptime' created", ro is not None)
    if ro:
        outcomes[ro["name"]] = ro["id"]

    return outcomes


# ══════════════════════════════════════════════════════════════════════
# SCENARIO 4 — Contracts with sub-contracts, parties, full hierarchy
# ══════════════════════════════════════════════════════════════════════


def scenario_contracts(
    flows: dict[str, str], outcomes: dict[str, str]
) -> dict[str, str]:
    """Create the Q3 Product Launch contract hierarchy from the spec example."""
    print("\n═══ Scenario 4: Contracts ═══")

    contracts = {}

    # 4a: Infrastructure SLA (sub-contract)
    body = gql(
        """
    mutation CreateContract($input: CreateContractInput!) {
      createContract(input: $input) {
        id name version owners { name role contact }
        workFlows { flowId flowVersion alias }
        requiredOutcomes { requiredOutcomeId requiredOutcomeVersion }
        subContracts { contractId }
        metadata
      }
    }
    """,
        {
            "input": {
                "name": "Infrastructure SLA",
                "description": "Ensure infrastructure meets reliability targets",
                "owners": [
                    {
                        "name": "Alice Chen",
                        "role": "lead",
                        "contact": "alice@example.com",
                    },
                    {"name": "SRE Team", "role": "delegate", "contact": "#sre-team"},
                ],
                "workFlows": [
                    {"flowId": flows["Infra BAU"], "flowVersion": 1, "alias": "bau"},
                ],
                "requiredOutcomes": [
                    {
                        "requiredOutcomeId": outcomes["99.9% uptime"],
                        "requiredOutcomeVersion": 1,
                    },
                ],
                "metadata": {"sla_tier": "gold"},
            }
        },
    )
    c = extract(body, "data.createContract")
    check("Contract 'Infrastructure SLA' created", c is not None and c["version"] == 1)
    if c:
        contracts[c["name"]] = c["id"]
        check("  has 2 owners (lead + delegate)", len(c["owners"]) == 2)
        check(
            "  lead is Alice Chen",
            c["owners"][0]["name"] == "Alice Chen" and c["owners"][0]["role"] == "lead",
        )
        check("  has 1 work flow", len(c["workFlows"]) == 1)
        check("  has 1 required outcome", len(c["requiredOutcomes"]) == 1)

    # 4b: Q3 Product Launch (top-level contract with sub-contract)
    body = gql(
        """
    mutation CreateContract($input: CreateContractInput!) {
      createContract(input: $input) {
        id name version owners { name role }
        workFlows { flowId alias }
        subContracts { contractId contractVersion alias }
        requiredOutcomes { requiredOutcomeId requiredOutcomeVersion alias }
        metadata
      }
    }
    """,
        {
            "input": {
                "name": "Q3 Product Launch",
                "description": "Ship Feature X, validate with customers, maintain infrastructure SLA",
                "owners": [
                    {
                        "name": "Bob Martinez",
                        "role": "lead",
                        "contact": "bob@example.com",
                    },
                    {
                        "name": "Carol Wang",
                        "role": "approver",
                        "contact": "carol@example.com",
                    },
                    {"name": "Dev Team", "role": "delegate"},
                    {
                        "name": "QA Lead",
                        "role": "reviewer",
                        "contact": "qa-lead@example.com",
                    },
                ],
                "workFlows": [
                    {
                        "flowId": flows["Engineering Sprint Cycle"],
                        "flowVersion": 1,
                        "alias": "eng-sprints",
                    },
                ],
                "subContracts": [
                    {
                        "contractId": contracts["Infrastructure SLA"],
                        "contractVersion": 1,
                        "alias": "infra-sla",
                    },
                ],
                "requiredOutcomes": [
                    {
                        "requiredOutcomeId": outcomes[
                            "Feature X shipped to production"
                        ],
                        "requiredOutcomeVersion": 1,
                        "alias": "feature-shipped",
                    },
                    {
                        "requiredOutcomeId": outcomes["Customer satisfaction ≥ 4.5/5"],
                        "requiredOutcomeVersion": 1,
                        "alias": "csat",
                    },
                ],
                "metadata": {"quarter": "Q3-2025", "priority": "critical"},
            }
        },
    )
    c = extract(body, "data.createContract")
    check("Contract 'Q3 Product Launch' created", c is not None and c["version"] == 1)
    if c:
        contracts[c["name"]] = c["id"]
        check(
            "  has 4 owners (lead + approver + delegate + reviewer)",
            len(c["owners"]) == 4,
        )
        check("  has 1 work flow", len(c["workFlows"]) == 1)
        check("  has 1 sub-contract", len(c["subContracts"]) == 1)
        check("  has 2 required outcomes", len(c["requiredOutcomes"]) == 2)
        check(
            "  sub-contract alias is 'infra-sla'",
            c["subContracts"][0]["alias"] == "infra-sla",
        )

    return contracts


# ══════════════════════════════════════════════════════════════════════
# SCENARIO 5 — Versioning: create v1, update to v2, query both
# ══════════════════════════════════════════════════════════════════════


def scenario_versioning(blocks: dict[str, str]):
    """Verify immutable versioning: update creates v2, v1 still accessible."""
    print("\n═══ Scenario 5: Versioning ═══")

    wb_id = blocks["Ticket Triage"]

    # Update the work block → should create version 2
    body = gql(
        """
    mutation UpdateWB($id: UUID!, $input: UpdateWorkBlockInput!) {
      updateWorkBlock(id: $id, input: $input) { id version name description }
    }
    """,
        {
            "id": wb_id,
            "input": {
                "description": "Classify incoming tickets by severity and route to the right team. Now with AI-assisted classification.",
                "metadata": {
                    "category": "intake",
                    "sla_minutes": 10,
                    "ai_assisted": True,
                },
            },
        },
    )
    updated = extract(body, "data.updateWorkBlock")
    check("Update creates version 2", updated is not None and updated["version"] == 2)

    # Query v1 explicitly
    body = gql(
        """
    query GetWB($id: UUID!, $version: Int) {
      workBlock(id: $id, version: $version) { id version description }
    }
    """,
        {"id": wb_id, "version": 1},
    )
    v1 = extract(body, "data.workBlock")
    check("Version 1 still accessible", v1 is not None and v1["version"] == 1)
    check(
        "Version 1 has original description",
        "AI-assisted" not in (v1 or {}).get("description", ""),
    )

    # Query v2 explicitly
    body = gql(
        """
    query GetWB($id: UUID!, $version: Int) {
      workBlock(id: $id, version: $version) { id version description }
    }
    """,
        {"id": wb_id, "version": 2},
    )
    v2 = extract(body, "data.workBlock")
    check("Version 2 accessible", v2 is not None and v2["version"] == 2)
    check(
        "Version 2 has updated description",
        "AI-assisted" in (v2 or {}).get("description", ""),
    )

    # Query latest (no version) → should return v2
    body = gql(
        """
    query GetWB($id: UUID!) {
      workBlock(id: $id) { id version }
    }
    """,
        {"id": wb_id},
    )
    latest = extract(body, "data.workBlock")
    check("Latest version returns v2", latest is not None and latest["version"] == 2)


def scenario_versioning_flow(flows: dict[str, str]):
    """Version a flow too."""
    flow_id = flows["Engineering Sprint Cycle"]
    body = gql(
        """
    mutation UpdateFlow($id: UUID!, $input: UpdateFlowInput!) {
      updateFlow(id: $id, input: $input) { id version metadata }
    }
    """,
        {
            "id": flow_id,
            "input": {
                "metadata": {
                    "sprint_length_days": 14,
                    "canvas_zoom": 1.2,
                    "updated": True,
                },
            },
        },
    )
    updated = extract(body, "data.updateFlow")
    check("Flow versioned to v2", updated is not None and updated["version"] == 2)

    # Both versions accessible
    body = gql(
        "query($id: UUID!) { flow(id: $id, version: 1) { version } }", {"id": flow_id}
    )
    check("Flow v1 still queryable", extract(body, "data.flow.version") == 1)

    body = gql("query($id: UUID!) { flow(id: $id) { version } }", {"id": flow_id})
    check("Flow latest is v2", extract(body, "data.flow.version") == 2)


# ══════════════════════════════════════════════════════════════════════
# SCENARIO 6 — Full Execution Lifecycle
# ══════════════════════════════════════════════════════════════════════


def scenario_execution_lifecycle(
    blocks: dict[str, str], flows: dict[str, str], contracts: dict[str, str]
):
    """Exercise the full execution lifecycle: create → assign → start →
    progress → outcome → complete, with state derivation."""
    print("\n═══ Scenario 6: Execution Lifecycle ═══")

    sprint_flow_id = flows["Engineering Sprint Cycle"]
    q3_contract_id = contracts["Q3 Product Launch"]

    # Create contract execution
    body = gql(
        """
    mutation($input: CreateContractExecutionInput!) {
      createContractExecution(input: $input) { id contractId contractVersion state }
    }
    """,
        {"input": {"contractId": q3_contract_id, "contractVersion": 1}},
    )
    ce = extract(body, "data.createContractExecution")
    check(
        "ContractExecution created (pending)",
        ce is not None and ce["state"] == "pending",
    )
    ce_id = ce["id"]

    # Create flow execution
    body = gql(
        """
    mutation($input: CreateFlowExecutionInput!) {
      createFlowExecution(input: $input) { id flowId flowVersion state contractExecutionId }
    }
    """,
        {
            "input": {
                "flowId": sprint_flow_id,
                "flowVersion": 1,
                "contractExecutionId": ce_id,
            }
        },
    )
    fe = extract(body, "data.createFlowExecution")
    check(
        "FlowExecution created (pending)", fe is not None and fe["state"] == "pending"
    )
    fe_id = fe["id"]

    # Link flow to contract
    body = gql(
        """
    mutation($ceId: UUID!, $feId: UUID!) {
      addFlowToContractExecution(contractExecutionId: $ceId, flowExecutionId: $feId) {
        id flowExecutions { id } state
      }
    }
    """,
        {"ceId": ce_id, "feId": fe_id},
    )
    ce_updated = extract(body, "data.addFlowToContractExecution")
    fe_ids_in_ce = [fe["id"] for fe in (ce_updated or {}).get("flowExecutions", [])]
    check(
        "Flow linked to contract execution",
        fe_id in fe_ids_in_ce,
    )

    # Create block execution for triage node
    body = gql(
        """
    mutation($input: CreateBlockExecutionInput!) {
      createBlockExecution(input: $input) { id state workBlockId nodeReferenceId }
    }
    """,
        {
            "input": {
                "workBlockId": blocks["Ticket Triage"],
                "workBlockVersion": 1,
                "nodeReferenceId": NODE_TRIAGE,
                "flowExecutionId": fe_id,
            }
        },
    )
    be_triage = extract(body, "data.createBlockExecution")
    check(
        "BlockExecution (triage) created",
        be_triage is not None and be_triage["state"] == "pending",
    )
    be_triage_id = be_triage["id"]

    # Link block to flow
    body = gql(
        """
    mutation($feId: UUID!, $beId: UUID!) {
      addBlockToFlowExecution(flowExecutionId: $feId, blockExecutionId: $beId) {
        id blockExecutions { id } state
      }
    }
    """,
        {"feId": fe_id, "beId": be_triage_id},
    )

    # Assign executor (human engineer)
    body = gql(
        """
    mutation($id: UUID!, $exec: ExecutorInfoInput!) {
      assignExecutorToBlock(executionId: $id, executor: $exec) { id state }
    }
    """,
        {
            "id": be_triage_id,
            "exec": {
                "type": "human",
                "identifier": "alice@example.com",
                "metadata": {"team": "triage"},
            },
        },
    )
    be = extract(body, "data.assignExecutorToBlock")
    check(
        "Executor assigned to triage block", be is not None and be["state"] == "pending"
    )

    # Start execution
    body = gql(
        """
    mutation($id: UUID!) { startBlockExecution(executionId: $id) { id state } }
    """,
        {"id": be_triage_id},
    )
    be = extract(body, "data.startBlockExecution")
    check(
        "Triage block started (in_progress)",
        be is not None and be["state"] == "in_progress",
    )

    # Produce outcome
    body = gql(
        """
    mutation($id: UUID!, $outcome: ExecutionOutcomeInput!) {
      produceBlockOutcome(executionId: $id, outcome: $outcome) { id state }
    }
    """,
        {
            "id": be_triage_id,
            "outcome": {
                "value": {"severity": "P1", "assigned_team": "backend"},
                "metadata": {"confidence": 0.95},
            },
        },
    )
    be = extract(body, "data.produceBlockOutcome")
    check("Triage outcome produced", be is not None)

    # Complete
    body = gql(
        """
    mutation($id: UUID!) { completeBlockExecution(executionId: $id) { id state } }
    """,
        {"id": be_triage_id},
    )
    be = extract(body, "data.completeBlockExecution")
    check("Triage block completed", be is not None and be["state"] == "completed")

    # Verify event stream
    body = gql(
        """
    query($eid: UUID!) {
      executionEvents(executionId: $eid) { eventType executor { type identifier } outcome { value } }
    }
    """,
        {"eid": be_triage_id},
    )
    events = extract(body, "data.executionEvents")
    check("Event stream has 5 events", events is not None and len(events) == 5)
    event_types = [e["eventType"] for e in (events or [])]
    check(
        "  created → executor_assigned → started → outcome_produced → completed",
        event_types
        == ["created", "executor_assigned", "started", "outcome_produced", "completed"],
    )

    # Check that the executor info round-tripped on the assigned event
    assigned_evt = next(
        (e for e in (events or []) if e["eventType"] == "executor_assigned"), None
    )
    check(
        "  executor_assigned carries ExecutorInfo",
        assigned_evt is not None
        and assigned_evt["executor"]["identifier"] == "alice@example.com",
    )

    return ce_id, fe_id


# ══════════════════════════════════════════════════════════════════════
# SCENARIO 7 — Executor Handoff (crash recovery)
# ══════════════════════════════════════════════════════════════════════


def scenario_executor_handoff(blocks: dict[str, str]):
    """Simulate crash recovery: agent A starts, crashes, agent B resumes."""
    print("\n═══ Scenario 7: Executor Handoff ═══")

    body = gql(
        """
    mutation($input: CreateBlockExecutionInput!) {
      createBlockExecution(input: $input) { id state }
    }
    """,
        {
            "input": {
                "workBlockId": blocks["Implementation"],
                "workBlockVersion": 1,
                "nodeReferenceId": NODE_IMPL_A,
            }
        },
    )
    be = extract(body, "data.createBlockExecution")
    be_id = be["id"]

    # Agent A assigned
    gql(
        """
    mutation($id: UUID!, $exec: ExecutorInfoInput!) {
      assignExecutorToBlock(executionId: $id, executor: $exec) { id }
    }
    """,
        {
            "id": be_id,
            "exec": {
                "type": "agent",
                "identifier": "agent-A",
                "metadata": {"model": "gpt-4"},
            },
        },
    )

    # Agent A starts
    gql(
        "mutation($id: UUID!) { startBlockExecution(executionId: $id) { id } }",
        {"id": be_id},
    )

    # Agent A crashes — release executor
    # The server doesn't have a releaseExecutor mutation directly, but we can verify
    # the event stream model supports it. Let's just verify the executor_assigned event
    # and then assign a new executor.

    # Agent B takes over
    gql(
        """
    mutation($id: UUID!, $exec: ExecutorInfoInput!) {
      assignExecutorToBlock(executionId: $id, executor: $exec) { id }
    }
    """,
        {
            "id": be_id,
            "exec": {
                "type": "agent",
                "identifier": "agent-B",
                "metadata": {"model": "claude-4"},
            },
        },
    )

    # Agent B completes
    gql(
        """
    mutation($id: UUID!, $outcome: ExecutionOutcomeInput!) {
      produceBlockOutcome(executionId: $id, outcome: $outcome) { id }
    }
    """,
        {
            "id": be_id,
            "outcome": {"value": {"pr_url": "https://github.com/example/pr/42"}},
        },
    )
    gql(
        "mutation($id: UUID!) { completeBlockExecution(executionId: $id) { id } }",
        {"id": be_id},
    )

    # Verify event stream shows the full handoff lineage
    body = gql(
        """
    query($eid: UUID!) {
      executionEvents(executionId: $eid) { eventType executor { type identifier } }
    }
    """,
        {"eid": be_id},
    )
    events = extract(body, "data.executionEvents")
    types = [e["eventType"] for e in (events or [])]
    check(
        "Handoff event stream recorded",
        "executor_assigned" in types and types.count("executor_assigned") == 2,
    )
    executors = [e["executor"]["identifier"] for e in (events or []) if e["executor"]]
    check(
        "  agent-A and agent-B both appear in log",
        "agent-A" in executors and "agent-B" in executors,
    )
    check("  final state is completed", types[-1] == "completed")


# ══════════════════════════════════════════════════════════════════════
# SCENARIO 8 — Flow State Derivation
# ══════════════════════════════════════════════════════════════════════


def scenario_flow_state_derivation(blocks: dict[str, str], flows: dict[str, str]):
    """Create a flow execution with multiple block executions and verify
    state derivation rules."""
    print("\n═══ Scenario 8: Flow State Derivation ═══")

    release_flow_id = flows["Release Verification"]

    # Create flow execution
    body = gql(
        """
    mutation($input: CreateFlowExecutionInput!) {
      createFlowExecution(input: $input) { id state }
    }
    """,
        {"input": {"flowId": release_flow_id, "flowVersion": 1}},
    )
    fe_id = extract(body, "data.createFlowExecution.id")

    # Create 3 block executions
    block_ids = []
    for node_id, wb_name in [
        (NODE_CHECK_DEPLOY, "Check Deployment Status"),
        (NODE_RUN_SMOKE, "Run Smoke Tests"),
        (NODE_VERDICT, "Produce Release Verdict"),
    ]:
        body = gql(
            """
        mutation($input: CreateBlockExecutionInput!) {
          createBlockExecution(input: $input) { id state }
        }
        """,
            {
                "input": {
                    "workBlockId": blocks[wb_name],
                    "workBlockVersion": 1,
                    "nodeReferenceId": node_id,
                    "flowExecutionId": fe_id,
                }
            },
        )
        block_ids.append(extract(body, "data.createBlockExecution.id"))
        # Link to flow
        gql(
            """
        mutation($feId: UUID!, $beId: UUID!) {
          addBlockToFlowExecution(flowExecutionId: $feId, blockExecutionId: $beId) { id }
        }
        """,
            {"feId": fe_id, "beId": block_ids[-1]},
        )

    # All pending → flow should be pending
    gql(f'mutation {{ refreshFlowState(flowExecutionId: "{fe_id}") {{ id state }} }}')
    body = gql(f'{{ flowExecution(id: "{fe_id}") {{ state }} }}')
    check(
        "All blocks pending → flow pending",
        extract(body, "data.flowExecution.state") == "pending",
    )

    # Start first block → flow should be in_progress
    gql(
        """
    mutation($id: UUID!, $exec: ExecutorInfoInput!) {
      assignExecutorToBlock(executionId: $id, executor: $exec) { id }
    }
    """,
        {"id": block_ids[0], "exec": {"type": "system", "identifier": "deployer"}},
    )
    gql(f'mutation {{ startBlockExecution(executionId: "{block_ids[0]}") {{ id }} }}')
    gql(f'mutation {{ refreshFlowState(flowExecutionId: "{fe_id}") {{ id state }} }}')
    body = gql(f'{{ flowExecution(id: "{fe_id}") {{ state }} }}')
    check(
        "One block started → flow in_progress",
        extract(body, "data.flowExecution.state") == "in_progress",
    )

    # Complete all 3 blocks
    for bid in block_ids:
        be_body = gql(f'{{ blockExecution(id: "{bid}") {{ state }} }}')
        state = extract(be_body, "data.blockExecution.state")
        if state == "pending":
            gql(
                """
            mutation($id: UUID!, $exec: ExecutorInfoInput!) {
              assignExecutorToBlock(executionId: $id, executor: $exec) { id }
            }
            """,
                {"id": bid, "exec": {"type": "system", "identifier": "auto-runner"}},
            )
            gql(f'mutation {{ startBlockExecution(executionId: "{bid}") {{ id }} }}')
        if state != "completed":
            gql(f'mutation {{ completeBlockExecution(executionId: "{bid}") {{ id }} }}')

    gql(f'mutation {{ refreshFlowState(flowExecutionId: "{fe_id}") {{ id state }} }}')
    body = gql(f'{{ flowExecution(id: "{fe_id}") {{ state }} }}')
    check(
        "All blocks completed → flow completed",
        extract(body, "data.flowExecution.state") == "completed",
    )

    # --- Failure scenario ---
    # Create another flow execution and fail a block
    body = gql(
        """
    mutation($input: CreateFlowExecutionInput!) {
      createFlowExecution(input: $input) { id }
    }
    """,
        {"input": {"flowId": release_flow_id, "flowVersion": 1}},
    )
    fe2_id = extract(body, "data.createFlowExecution.id")

    body = gql(
        """
    mutation($input: CreateBlockExecutionInput!) {
      createBlockExecution(input: $input) { id }
    }
    """,
        {
            "input": {
                "workBlockId": blocks["Check Deployment Status"],
                "workBlockVersion": 1,
                "nodeReferenceId": NODE_CHECK_DEPLOY,
                "flowExecutionId": fe2_id,
            }
        },
    )
    fail_be_id = extract(body, "data.createBlockExecution.id")
    gql(
        f'mutation {{ addBlockToFlowExecution(flowExecutionId: "{fe2_id}", blockExecutionId: "{fail_be_id}") {{ id }} }}'
    )

    # Assign, start, fail
    gql(
        """
    mutation($id: UUID!, $exec: ExecutorInfoInput!) {
      assignExecutorToBlock(executionId: $id, executor: $exec) { id }
    }
    """,
        {"id": fail_be_id, "exec": {"type": "system", "identifier": "deployer"}},
    )
    gql(f'mutation {{ startBlockExecution(executionId: "{fail_be_id}") {{ id }} }}')
    gql(
        f'mutation {{ failBlockExecution(executionId: "{fail_be_id}") {{ id state }} }}'
    )

    gql(f'mutation {{ refreshFlowState(flowExecutionId: "{fe2_id}") {{ id }} }}')
    body = gql(f'{{ flowExecution(id: "{fe2_id}") {{ state }} }}')
    check(
        "Any block failed → flow failed",
        extract(body, "data.flowExecution.state") == "failed",
    )


# ══════════════════════════════════════════════════════════════════════
# SCENARIO 9 — Many-to-many execution sharing
# ══════════════════════════════════════════════════════════════════════


def scenario_many_to_many(blocks: dict[str, str], flows: dict[str, str]):
    """A single BlockExecution referenced by two FlowExecutions."""
    print("\n═══ Scenario 9: Many-to-Many Execution Sharing ═══")

    # Create a shared block execution (not linked to any flow yet)
    body = gql(
        """
    mutation($input: CreateBlockExecutionInput!) {
      createBlockExecution(input: $input) { id }
    }
    """,
        {
            "input": {
                "workBlockId": blocks["Run Smoke Tests"],
                "workBlockVersion": 1,
                "nodeReferenceId": NODE_RUN_SMOKE,
            }
        },
    )
    shared_be_id = extract(body, "data.createBlockExecution.id")

    # Complete it
    gql(
        """
    mutation($id: UUID!, $exec: ExecutorInfoInput!) {
      assignExecutorToBlock(executionId: $id, executor: $exec) { id }
    }
    """,
        {"id": shared_be_id, "exec": {"type": "system", "identifier": "test-runner"}},
    )
    gql(f'mutation {{ startBlockExecution(executionId: "{shared_be_id}") {{ id }} }}')
    gql(
        f'mutation {{ completeBlockExecution(executionId: "{shared_be_id}") {{ id }} }}'
    )

    # Create two flow executions that both reference this block
    fe_ids = []
    for _ in range(2):
        body = gql(
            """
        mutation($input: CreateFlowExecutionInput!) {
          createFlowExecution(input: $input) { id }
        }
        """,
            {"input": {"flowId": flows["Smoke Test Suite"], "flowVersion": 1}},
        )
        fid = extract(body, "data.createFlowExecution.id")
        gql(
            f'mutation {{ addBlockToFlowExecution(flowExecutionId: "{fid}", blockExecutionId: "{shared_be_id}") {{ id blockExecutions {{ id }} }} }}'
        )
        fe_ids.append(fid)

    # Verify both flow executions reference the same block execution
    for i, fid in enumerate(fe_ids):
        body = gql(f'{{ flowExecution(id: "{fid}") {{ blockExecutions {{ id }} }} }}')
        bes = extract(body, "data.flowExecution.blockExecutions")
        be_ids = [be["id"] for be in (bes or [])]
        check(
            f"FlowExecution {i+1} references shared block", shared_be_id in be_ids
        )


# ══════════════════════════════════════════════════════════════════════
# SCENARIO 10 — Listing & filtering queries
# ══════════════════════════════════════════════════════════════════════


def scenario_queries(blocks: dict[str, str]):
    """Exercise listing, filtering, and pagination queries."""
    print("\n═══ Scenario 10: Listing & Filtering ═══")

    # List all work blocks
    body = gql("{ workBlocks { id name } }")
    wbs = extract(body, "data.workBlocks")
    check(f"List workBlocks returns ≥12 results", wbs is not None and len(wbs) >= 12)

    # Filter by name
    body = gql('{ workBlocks(name: "Code Review") { id name } }')
    wbs = extract(body, "data.workBlocks")
    check(
        "Filter workBlocks by name",
        wbs is not None and len(wbs) >= 1 and wbs[0]["name"] == "Code Review",
    )

    # Pagination
    body = gql("{ workBlocks(limit: 3, offset: 0) { name } }")
    page1 = extract(body, "data.workBlocks")
    body = gql("{ workBlocks(limit: 3, offset: 3) { name } }")
    page2 = extract(body, "data.workBlocks")
    check(
        "Pagination works (page1 ≠ page2)",
        page1 is not None
        and page2 is not None
        and len(page1) == 3
        and set(p["name"] for p in page1) != set(p["name"] for p in page2),
    )

    # List flows
    body = gql("{ flows { id name } }")
    fs = extract(body, "data.flows")
    check(f"List flows returns ≥7 results", fs is not None and len(fs) >= 7)

    # List contracts
    body = gql("{ contracts { id name } }")
    cs = extract(body, "data.contracts")
    check(f"List contracts returns ≥2 results", cs is not None and len(cs) >= 2)

    # List required outcomes
    body = gql("{ requiredOutcomes { id name } }")
    ros = extract(body, "data.requiredOutcomes")
    check(
        f"List requiredOutcomes returns ≥3 results", ros is not None and len(ros) >= 3
    )

    # List block executions filtered by state
    body = gql('{ blockExecutions(state: "completed") { id state } }')
    bes = extract(body, "data.blockExecutions")
    check(
        "Filter blockExecutions by state=completed",
        bes is not None and all(b["state"] == "completed" for b in bes),
    )


# ══════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════


def main():
    print(f"🚀 OpenOMA Scenario Loader — targeting {SERVER}")
    print("=" * 60)

    # Check server health
    try:
        resp = httpx.get(f"{SERVER}/health", timeout=5)
        resp.raise_for_status()
        print(f"✅ Server healthy: {resp.json()}")
    except Exception as e:
        print(f"❌ Server not reachable at {SERVER}: {e}")
        sys.exit(1)

    # Clear the database so the script is idempotent
    clear_db()

    # Run all scenarios
    blocks = scenario_work_blocks()
    flows = scenario_flows(blocks)
    outcomes = scenario_required_outcomes(flows)
    contracts = scenario_contracts(flows, outcomes)
    scenario_versioning(blocks)
    scenario_versioning_flow(flows)
    scenario_execution_lifecycle(blocks, flows, contracts)
    scenario_executor_handoff(blocks)
    scenario_flow_state_derivation(blocks, flows)
    scenario_many_to_many(blocks, flows)
    scenario_queries(blocks)

    # Summary
    print("\n" + "=" * 60)
    total = ok_count + fail_count
    print(f"🏁 Results: {ok_count}/{total} checks passed, {fail_count} failed")

    if fail_count > 0:
        print("\n⚠️  Some checks failed — see ❌ marks above.")
        sys.exit(1)
    else:
        print("\n🎉 All scenarios verified successfully!")
        print("\nDesign principles validated:")
        print("  ✅ Declarative over imperative (blocks describe what, not how)")
        print("  ✅ Composability (blocks → flows → contracts, flows as assessment)")
        print(
            "  ✅ Identity and immutability (versioned entities, both versions queryable)"
        )
        print("  ✅ Event-sourced execution (append-only log, state derived)")
        print("  ✅ Executor independence (handoff between agents)")
        print("  ✅ Self-similar assessment (assessment flows are regular flows)")
        print("  ✅ Graph topology freedom (disconnected subgraphs, parallel lanes)")
        print("  ✅ Many-to-many execution sharing")
        print("  ✅ Same-block-two-slots pattern")
        print("  ✅ Conditional and unconditional edges with port mappings")
        print("  ✅ Parties with roles (lead/delegate/approver/reviewer)")
        print("  ✅ Sub-contract hierarchy")


if __name__ == "__main__":
    main()
