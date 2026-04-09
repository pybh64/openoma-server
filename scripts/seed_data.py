#!/usr/bin/env python3
"""Seed the OpenOMA database via the local GraphQL API with realistic example data.

Usage:
    uv run python scripts/seed_data.py              # default: http://localhost:8000
    uv run python scripts/seed_data.py --url http://localhost:9000/graphql

Scenarios covered:
    1. Simple work blocks (atomic tasks with ports)
    2. Work blocks with rich metadata and schema-validated ports
    3. Flows that compose work blocks into DAGs (linear, branching, conditional)
    4. Assessment flows for quality gates
    5. Contracts that bind flows + sub-contracts + required outcomes
    6. Versioned updates (work block v1 → v2, flow v1 → v2)
    7. Full execution lifecycle (block → flow → contract)
    8. Execution events: assign, start, progress, outcome, complete, fail, cancel
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from urllib.request import Request, urlopen
from uuid import uuid4

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

API_URL = "http://localhost:8000/graphql"


def gql(query: str, variables: dict[str, Any] | None = None) -> dict:
    """Send a GraphQL request and return the response data, aborting on errors."""
    body: dict[str, Any] = {"query": query}
    if variables:
        body["variables"] = variables
    req = Request(
        API_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(req) as resp:
        result = json.loads(resp.read())
    if "errors" in result:
        print(f"❌ GraphQL errors:\n{json.dumps(result['errors'], indent=2)}", file=sys.stderr)
        print(f"   Query: {query[:120]}…", file=sys.stderr)
        sys.exit(1)
    return result["data"]


def to_gql_value(value: Any) -> str:
    """Convert a Python value to a GraphQL literal (unquoted keys for objects)."""
    if isinstance(value, dict):
        pairs = [f"{k}: {to_gql_value(v)}" for k, v in value.items()]
        return "{" + ", ".join(pairs) + "}"
    if isinstance(value, list):
        return "[" + ", ".join(to_gql_value(v) for v in value) + "]"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if value is None:
        return "null"
    return json.dumps(value)


def heading(text: str) -> None:
    print(f"\n{'='*60}\n  {text}\n{'='*60}")


# ---------------------------------------------------------------------------
# 1. Work Blocks — atomic units of work
# ---------------------------------------------------------------------------


def create_work_blocks() -> dict[str, dict]:
    heading("1 · Creating Work Blocks")

    blocks: dict[str, dict] = {}

    # --- 1a. Minimal block (no ports, no hints) ---
    data = gql("""
    mutation {
        createWorkBlock(input: {
            name: "Placeholder Task"
            description: "An empty block used as a template"
        }) { id version name }
    }
    """)
    b = data["createWorkBlock"]
    blocks["placeholder"] = b
    print(f"  ✔ {b['name']} (id={b['id']}, v{b['version']})")

    # --- 1b. Data ingestion block with typed ports ---
    data = gql("""
    mutation {
        createWorkBlock(input: {
            name: "Ingest CSV Data"
            description: "Read a CSV file and emit structured rows"
            inputs: [
                {name: "file_path", description: "Path to the CSV file", required: true,
                 schemaDef: {type: "string", format: "file-path"}}
                {name: "delimiter", description: "Column delimiter", required: false,
                 schemaDef: {type: "string", default: ","}}
            ]
            outputs: [
                {name: "rows", description: "Parsed rows as JSON array", required: true,
                 schemaDef: {type: "array", items: {type: "object"}}}
                {name: "row_count", description: "Total number of rows", required: true,
                 schemaDef: {type: "integer"}}
            ]
            executionHints: ["cpu-bound", "disk-io"]
            metadata: {category: "data-engineering", runtime: "python3.12"}
        }) { id version name inputs { name required } outputs { name } executionHints }
    }
    """)
    b = data["createWorkBlock"]
    blocks["ingest_csv"] = b
    print(f"  ✔ {b['name']} (id={b['id']}, v{b['version']}, "
          f"{len(b['inputs'])} in / {len(b['outputs'])} out)")

    # --- 1c. Data validation block ---
    data = gql("""
    mutation {
        createWorkBlock(input: {
            name: "Validate Data Quality"
            description: "Run data quality checks: nulls, ranges, uniqueness"
            inputs: [
                {name: "rows", description: "Input rows to validate", required: true}
                {name: "rules", description: "Validation rule set (JSON)", required: true,
                 schemaDef: {type: "object"}}
            ]
            outputs: [
                {name: "valid_rows", description: "Rows that passed all checks"}
                {name: "rejected_rows", description: "Rows that failed checks"}
                {name: "report", description: "Validation summary report",
                 schemaDef: {type: "object", properties: {total: {type: "integer"},
                             passed: {type: "integer"}, failed: {type: "integer"}}}}
            ]
            executionHints: ["cpu-bound"]
            metadata: {category: "data-engineering", severity: "critical"}
        }) { id version name }
    }
    """)
    blocks["validate"] = data["createWorkBlock"]
    print(f"  ✔ {blocks['validate']['name']}")

    # --- 1d. ML training block ---
    data = gql("""
    mutation {
        createWorkBlock(input: {
            name: "Train ML Model"
            description: "Train a scikit-learn model on the provided dataset"
            inputs: [
                {name: "training_data", description: "Feature matrix (rows)", required: true}
                {name: "hyperparams", description: "Model hyperparameters", required: false,
                 schemaDef: {type: "object"}, metadata: {example: {n_estimators: 100}}}
            ]
            outputs: [
                {name: "model_artifact", description: "Serialised model bytes"}
                {name: "metrics", description: "Training metrics",
                 schemaDef: {type: "object", properties: {
                     accuracy: {type: "number"}, f1: {type: "number"}}}}
            ]
            executionHints: ["gpu-preferred", "long-running"]
            metadata: {category: "ml", framework: "scikit-learn", estimated_minutes: 30}
        }) { id version name }
    }
    """)
    blocks["train_model"] = data["createWorkBlock"]
    print(f"  ✔ {blocks['train_model']['name']}")

    # --- 1e. Model evaluation block ---
    data = gql("""
    mutation {
        createWorkBlock(input: {
            name: "Evaluate Model"
            description: "Score the model against a held-out test set"
            inputs: [
                {name: "model_artifact", description: "The trained model", required: true}
                {name: "test_data", description: "Held-out test rows", required: true}
            ]
            outputs: [
                {name: "score_report", description: "Detailed scoring report",
                 schemaDef: {type: "object"}}
                {name: "passed", description: "Whether quality gate passed",
                 schemaDef: {type: "boolean"}}
            ]
            executionHints: ["cpu-bound"]
            metadata: {category: "ml", stage: "evaluation"}
        }) { id version name }
    }
    """)
    blocks["evaluate_model"] = data["createWorkBlock"]
    print(f"  ✔ {blocks['evaluate_model']['name']}")

    # --- 1f. Notification block ---
    data = gql("""
    mutation {
        createWorkBlock(input: {
            name: "Send Notification"
            description: "Send a Slack or email notification"
            inputs: [
                {name: "channel", description: "Notification channel (slack / email)", required: true,
                 schemaDef: {type: "string", enum: ["slack", "email"]}}
                {name: "message", description: "Message body", required: true}
                {name: "recipients", description: "List of recipients", required: false,
                 schemaDef: {type: "array", items: {type: "string"}}}
            ]
            outputs: [
                {name: "delivery_id", description: "Tracking ID for the notification"}
            ]
            executionHints: ["network-io", "idempotent"]
            metadata: {category: "ops", retryable: true}
        }) { id version name }
    }
    """)
    blocks["notify"] = data["createWorkBlock"]
    print(f"  ✔ {blocks['notify']['name']}")

    # --- 1g. Deploy block ---
    data = gql("""
    mutation {
        createWorkBlock(input: {
            name: "Deploy to Production"
            description: "Push a model artifact to the production serving endpoint"
            inputs: [
                {name: "model_artifact", description: "Serialised model", required: true}
                {name: "target_env", description: "Target environment", required: true,
                 schemaDef: {type: "string", enum: ["staging", "production"]}}
            ]
            outputs: [
                {name: "deployment_url", description: "Live endpoint URL"}
                {name: "rollback_id", description: "ID for rollback if needed"}
            ]
            executionHints: ["network-io", "requires-approval"]
            metadata: {category: "ops", risk: "high"}
        }) { id version name }
    }
    """)
    blocks["deploy"] = data["createWorkBlock"]
    print(f"  ✔ {blocks['deploy']['name']}")

    print(f"\n  → Created {len(blocks)} work blocks")
    return blocks


# ---------------------------------------------------------------------------
# 2. Version updates — demonstrate immutable versioning
# ---------------------------------------------------------------------------


def create_versioned_updates(blocks: dict[str, dict]) -> dict[str, dict]:
    heading("2 · Versioned Updates")

    # Update the ingest block: add a new output port
    block_id = blocks["ingest_csv"]["id"]
    data = gql(f"""
    mutation {{
        updateWorkBlock(input: {{
            id: "{block_id}"
            name: "Ingest CSV Data"
            description: "Read a CSV file and emit structured rows (v2: added schema output)"
            inputs: [
                {{name: "file_path", description: "Path to the CSV file", required: true}}
                {{name: "delimiter", description: "Column delimiter", required: false}}
                {{name: "encoding", description: "File encoding (new in v2)", required: false,
                 schemaDef: {{type: "string", default: "utf-8"}}}}
            ]
            outputs: [
                {{name: "rows", description: "Parsed rows"}}
                {{name: "row_count", description: "Total number of rows"}}
                {{name: "inferred_schema", description: "Auto-detected column types (new in v2)"}}
            ]
            executionHints: ["cpu-bound", "disk-io"]
            metadata: {{category: "data-engineering", runtime: "python3.12",
                        changelog: "added encoding input and inferred_schema output"}}
        }}) {{ id version name }}
    }}
    """)
    b = data["updateWorkBlock"]
    blocks["ingest_csv_v2"] = b
    print(f"  ✔ Updated '{b['name']}' → v{b['version']}")

    # Update placeholder block: give it real meaning
    block_id = blocks["placeholder"]["id"]
    data = gql(f"""
    mutation {{
        updateWorkBlock(input: {{
            id: "{block_id}"
            name: "Archive Results"
            description: "Compress and archive pipeline outputs to cold storage"
            inputs: [
                {{name: "artifacts", description: "List of artifact paths to archive",
                  required: true}}
            ]
            outputs: [
                {{name: "archive_uri", description: "URI of the created archive"}}
            ]
            executionHints: ["disk-io", "network-io"]
            metadata: {{category: "ops"}}
        }}) {{ id version name }}
    }}
    """)
    b = data["updateWorkBlock"]
    blocks["archive"] = b
    print(f"  ✔ Updated 'Placeholder Task' → '{b['name']}' v{b['version']}")

    return blocks


# ---------------------------------------------------------------------------
# 3. Flows — compose blocks into DAGs
# ---------------------------------------------------------------------------


def create_flows(blocks: dict[str, dict]) -> dict[str, dict]:
    heading("3 · Creating Flows")

    flows: dict[str, dict] = {}

    ingest_id = blocks["ingest_csv"]["id"]
    validate_id = blocks["validate"]["id"]
    train_id = blocks["train_model"]["id"]
    eval_id = blocks["evaluate_model"]["id"]
    notify_id = blocks["notify"]["id"]
    deploy_id = blocks["deploy"]["id"]

    # --- 3a. Linear ETL flow: Ingest → Validate → Notify ---
    # Pre-generate node reference IDs so edges can reference them
    n_ingest, n_validate, n_notify = uuid4(), uuid4(), uuid4()
    data = gql(f"""
    mutation {{
        createFlow(input: {{
            name: "Simple ETL Pipeline"
            description: "Ingest CSV data, validate quality, and notify on completion"
            nodes: [
                {{id: "{n_ingest}", targetId: "{ingest_id}", targetVersion: 1,
                  alias: "ingest"}}
                {{id: "{n_validate}", targetId: "{validate_id}", targetVersion: 1,
                  alias: "validate"}}
                {{id: "{n_notify}", targetId: "{notify_id}", targetVersion: 1,
                  alias: "notify_done"}}
            ]
            edges: [
                {{sourceId: "{n_ingest}", targetId: "{n_validate}",
                  portMappings: [{{sourcePort: "rows", targetPort: "rows"}}]}}
                {{sourceId: "{n_validate}", targetId: "{n_notify}"}}
            ]
            expectedOutcome: {{type: "data_validated", minPassRate: 0.95}}
            metadata: {{team: "data-eng", sla_minutes: 15}}
        }}) {{ id version name nodes {{ id alias targetId }} edges {{ sourceId targetId }} }}
    }}
    """)
    f = data["createFlow"]
    flows["etl_simple"] = f
    print(f"  ✔ {f['name']} (id={f['id']}, {len(f['nodes'])} nodes, {len(f['edges'])} edges)")

    # --- 3b. Branching ML flow: Ingest → Validate → Train → Evaluate → Deploy/Notify ---
    n_ingest2 = uuid4()
    n_validate2 = uuid4()
    n_train = uuid4()
    n_eval = uuid4()
    n_deploy = uuid4()
    n_notify2 = uuid4()
    data = gql(f"""
    mutation {{
        createFlow(input: {{
            name: "ML Training Pipeline"
            description: "End-to-end ML pipeline with conditional deployment"
            nodes: [
                {{id: "{n_ingest2}", targetId: "{ingest_id}", targetVersion: 1,
                  alias: "ingest"}}
                {{id: "{n_validate2}", targetId: "{validate_id}", targetVersion: 1,
                  alias: "validate"}}
                {{id: "{n_train}", targetId: "{train_id}", targetVersion: 1,
                  alias: "train"}}
                {{id: "{n_eval}", targetId: "{eval_id}", targetVersion: 1,
                  alias: "evaluate"}}
                {{id: "{n_deploy}", targetId: "{deploy_id}", targetVersion: 1,
                  alias: "deploy"}}
                {{id: "{n_notify2}", targetId: "{notify_id}", targetVersion: 1,
                  alias: "notify_result"}}
            ]
            edges: [
                {{sourceId: "{n_ingest2}", targetId: "{n_validate2}",
                  portMappings: [{{sourcePort: "rows", targetPort: "rows"}}]}}
                {{sourceId: "{n_validate2}", targetId: "{n_train}",
                  portMappings: [{{sourcePort: "valid_rows",
                                   targetPort: "training_data"}}]}}
                {{sourceId: "{n_train}", targetId: "{n_eval}",
                  portMappings: [
                    {{sourcePort: "model_artifact", targetPort: "model_artifact"}}
                  ]}}
                {{sourceId: "{n_eval}", targetId: "{n_deploy}",
                  condition: {{
                    description: "Deploy only if evaluation passed",
                    predicate: {{field: "passed", op: "eq", value: true}}
                  }},
                  portMappings: [{{sourcePort: "model_artifact",
                                   targetPort: "model_artifact"}}]}}
                {{sourceId: "{n_eval}", targetId: "{n_notify2}"}}
            ]
            expectedOutcome: {{type: "model_deployed", minAccuracy: 0.85}}
            metadata: {{team: "ml-platform", priority: "high"}}
        }}) {{ id version name nodes {{ id alias }} }}
    }}
    """)
    f = data["createFlow"]
    flows["ml_pipeline"] = f
    print(f"  ✔ {f['name']} (id={f['id']}, {len(f['nodes'])} nodes)")

    # --- 3c. Assessment flow (quality gate) ---
    data = gql(f"""
    mutation {{
        createFlow(input: {{
            name: "Model Quality Assessment"
            description: "Assessment flow that evaluates whether a trained model meets the production bar"
            nodes: [
                {{targetId: "{eval_id}", targetVersion: 1, alias: "run_evaluation"}}
            ]
            edges: []
            isAssessment: true
            expectedOutcome: {{minAccuracy: 0.90, minF1: 0.85}}
            metadata: {{type: "quality-gate", stage: "pre-deploy"}}
        }}) {{ id version name }}
    }}
    """)
    flows["assessment_quality"] = data["createFlow"]
    print(f"  ✔ {flows['assessment_quality']['name']} (assessment)")

    # --- 3d. Minimal monitoring flow ---
    n_drift = uuid4()
    n_alert = uuid4()
    data = gql(f"""
    mutation {{
        createFlow(input: {{
            name: "Drift Monitoring"
            description: "Periodic check for data/model drift in production"
            nodes: [
                {{id: "{n_drift}", targetId: "{eval_id}", targetVersion: 1,
                  alias: "check_drift"}}
                {{id: "{n_alert}", targetId: "{notify_id}", targetVersion: 1,
                  alias: "alert"}}
            ]
            edges: [
                {{sourceId: "{n_drift}", targetId: "{n_alert}"}}
            ]
            metadata: {{schedule: "0 */6 * * *", team: "ml-ops"}}
        }}) {{ id version name }}
    }}
    """)
    flows["monitoring"] = data["createFlow"]
    print(f"  ✔ {flows['monitoring']['name']}")

    # --- 3e. Update ETL flow (v2 — uses ingest_csv v2) ---
    etl_id = flows["etl_simple"]["id"]
    node_ids = {n["alias"]: n["id"] for n in flows["etl_simple"]["nodes"]}
    data = gql(f"""
    mutation {{
        updateFlow(input: {{
            id: "{etl_id}"
            name: "Simple ETL Pipeline"
            description: "v2: uses Ingest CSV v2 with encoding support"
            nodes: [
                {{id: "{node_ids['ingest']}", targetId: "{ingest_id}",
                  targetVersion: 2, alias: "ingest"}}
                {{id: "{node_ids['validate']}", targetId: "{validate_id}",
                  targetVersion: 1, alias: "validate"}}
                {{id: "{node_ids['notify_done']}", targetId: "{notify_id}",
                  targetVersion: 1, alias: "notify_done"}}
            ]
            edges: [
                {{sourceId: "{node_ids['ingest']}", targetId: "{node_ids['validate']}",
                  portMappings: [{{sourcePort: "rows", targetPort: "rows"}}]}}
                {{sourceId: "{node_ids['validate']}", targetId: "{node_ids['notify_done']}"}}
            ]
            metadata: {{team: "data-eng", sla_minutes: 15,
                        changelog: "upgraded ingest to v2"}}
        }}) {{ id version name }}
    }}
    """)
    f = data["updateFlow"]
    flows["etl_simple_v2"] = f
    print(f"  ✔ Updated ETL flow → v{f['version']}")

    print(f"\n  → Created/updated {len(flows)} flows")
    return flows


# ---------------------------------------------------------------------------
# 4. Contracts — bind flows together with outcomes & assessments
# ---------------------------------------------------------------------------


def create_contracts(flows: dict[str, dict]) -> dict[str, dict]:
    heading("4 · Creating Contracts")

    contracts: dict[str, dict] = {}

    etl_id = flows["etl_simple"]["id"]
    ml_id = flows["ml_pipeline"]["id"]
    monitor_id = flows["monitoring"]["id"]

    # --- 4a. Simple contract: just one flow ---
    data = gql(f"""
    mutation {{
        createContract(input: {{
            name: "Daily ETL Contract"
            description: "Ensure daily data ingestion completes with >95% pass rate"
            workFlows: [
                {{flowId: "{etl_id}", flowVersion: 1, alias: "daily_etl"}}
            ]
            requiredOutcomes: [
                {{name: "Data Freshness",
                  description: "Data ingested within SLA window"}}
                {{name: "Quality Threshold",
                  description: "At least 95% of rows pass validation"}}
            ]
            metadata: {{schedule: "daily", owner: "data-eng-team"}}
        }}) {{ id version name requiredOutcomes {{ id name }} }}
    }}
    """)
    c = data["createContract"]
    contracts["etl_contract"] = c
    print(f"  ✔ {c['name']} (id={c['id']}, {len(c['requiredOutcomes'])} outcomes)")

    # --- 4b. ML contract with assessment binding ---
    data = gql(f"""
    mutation {{
        createContract(input: {{
            name: "ML Model Release Contract"
            description: "Full ML lifecycle: train, evaluate, and deploy with quality gate"
            workFlows: [
                {{flowId: "{ml_id}", flowVersion: 1, alias: "training_pipeline"}}
                {{flowId: "{monitor_id}", flowVersion: 1, alias: "drift_monitor"}}
            ]
            requiredOutcomes: [
                {{name: "Model Accuracy",
                  description: "Model accuracy ≥ 90% on test set"}}
                {{name: "No Data Drift",
                  description: "Feature distributions within tolerance"}}
                {{name: "Deployment Success",
                  description: "Model deployed and serving traffic"}}
            ]
            metadata: {{team: "ml-platform", criticality: "p0",
                        approvers: ["lead-ds", "ml-ops"]}}
        }}) {{ id version name requiredOutcomes {{ id name }} }}
    }}
    """)
    c = data["createContract"]
    contracts["ml_contract"] = c
    print(f"  ✔ {c['name']} ({len(c['requiredOutcomes'])} outcomes)")

    # --- 4c. Master contract with sub-contracts ---
    data = gql(f"""
    mutation {{
        createContract(input: {{
            name: "Quarterly ML Review"
            description: "Top-level contract aggregating ETL + ML sub-contracts"
            subContracts: [
                {{contractId: "{contracts['etl_contract']['id']}",
                  contractVersion: 1, alias: "etl"}}
                {{contractId: "{contracts['ml_contract']['id']}",
                  contractVersion: 1, alias: "ml_release"}}
            ]
            requiredOutcomes: [
                {{name: "All Pipelines Healthy",
                  description: "Both ETL and ML pipelines green"}}
                {{name: "Stakeholder Sign-off",
                  description: "Product owner has approved results"}}
            ]
            metadata: {{cadence: "quarterly", department: "engineering"}}
        }}) {{ id version name subContracts {{ contractId alias }} }}
    }}
    """)
    c = data["createContract"]
    contracts["master_contract"] = c
    print(f"  ✔ {c['name']} (sub-contracts: {len(c['subContracts'])})")

    print(f"\n  → Created {len(contracts)} contracts")
    return contracts


# ---------------------------------------------------------------------------
# 5. Executions — lifecycle scenarios
# ---------------------------------------------------------------------------


def create_executions(
    blocks: dict[str, dict],
    flows: dict[str, dict],
    contracts: dict[str, dict],
) -> None:
    heading("5 · Execution Lifecycle Scenarios")

    ingest_id = blocks["ingest_csv"]["id"]
    validate_id = blocks["validate"]["id"]
    train_id = blocks["train_model"]["id"]
    notify_id = blocks["notify"]["id"]
    etl_flow = flows["etl_simple"]
    ml_flow = flows["ml_pipeline"]
    ml_contract = contracts["ml_contract"]

    etl_node_ids = {n["alias"]: n["id"] for n in etl_flow.get("nodes", [])}

    # ── 5a. Successful block execution (happy path) ──
    print("\n  ── 5a. Successful block execution ──")

    data = gql(f"""
    mutation {{
        startBlockExecution(input: {{
            nodeReferenceId: "{etl_node_ids.get('ingest', '00000000-0000-0000-0000-000000000001')}"
            workBlockId: "{ingest_id}"
            workBlockVersion: 1
            executorType: "human"
            executorId: "alice@example.com"
        }}) {{ id state events {{ eventType }} }}
    }}
    """)
    be = data["startBlockExecution"]
    be_id = be["id"]
    print(f"  ✔ Block execution created: {be_id} (state={be['state']})")

    for event in [
        {
            "eventType": "executor_assigned",
            "executorType": "human",
            "executorId": "alice@example.com",
            "metadata": {"assignedAt": "2026-04-09T10:00:00Z"},
        },
        {
            "eventType": "started",
            "executorType": "human",
            "executorId": "alice@example.com",
        },
        {
            "eventType": "progress",
            "payload": {"percent": 50, "rowsProcessed": 5000, "totalRows": 10000},
            "metadata": {"checkpoint": "halfway"},
        },
        {
            "eventType": "progress",
            "payload": {"percent": 100, "rowsProcessed": 10000, "totalRows": 10000},
        },
        {
            "eventType": "outcome_produced",
            "payload": {
                "row_count": 10000,
                "inferred_schema": {"col_a": "int", "col_b": "string"},
            },
        },
        {
            "eventType": "completed",
            "metadata": {"durationSeconds": 42},
        },
    ]:
        _emit_event(be_id, event)

    # ── 5b. Failed block execution ──
    print("\n  ── 5b. Failed block execution ──")

    data = gql(f"""
    mutation {{
        startBlockExecution(input: {{
            nodeReferenceId: "{etl_node_ids.get('validate', '00000000-0000-0000-0000-000000000002')}"
            workBlockId: "{validate_id}"
            workBlockVersion: 1
            executorType: "system"
            executorId: "validator-agent-v3"
        }}) {{ id state }}
    }}
    """)
    failed_be_id = data["startBlockExecution"]["id"]
    print(f"  ✔ Block execution created: {failed_be_id}")

    for event in [
        {"eventType": "started"},
        {
            "eventType": "failed",
            "payload": {
                "error": "ValidationError",
                "message": "42 rows failed null-check on column 'email'",
                "failedRows": 42,
                "totalRows": 10000,
            },
            "metadata": {"retriable": True, "suggestedAction": "fix source data"},
        },
    ]:
        _emit_event(failed_be_id, event)

    # ── 5c. Cancelled block execution ──
    print("\n  ── 5c. Cancelled block execution ──")

    data = gql(f"""
    mutation {{
        startBlockExecution(input: {{
            nodeReferenceId: "{etl_node_ids.get('notify_done', '00000000-0000-0000-0000-000000000003')}"
            workBlockId: "{notify_id}"
            workBlockVersion: 1
            executorType: "human"
            executorId: "bob@example.com"
        }}) {{ id state }}
    }}
    """)
    cancelled_be_id = data["startBlockExecution"]["id"]

    for event in [
        {
            "eventType": "executor_assigned",
            "executorType": "human",
            "executorId": "bob@example.com",
        },
        {
            "eventType": "cancelled",
            "payload": {
                "reason": "Upstream pipeline failed — notification no longer needed"
            },
            "metadata": {"cancelledBy": "bob@example.com"},
        },
    ]:
        _emit_event(cancelled_be_id, event)
    print(f"  ✔ Block {cancelled_be_id}: assigned → cancelled")

    # ── 5d. Flow execution (ETL) ──
    print("\n  ── 5d. Flow execution (ETL) ──")

    data = gql(f"""
    mutation {{
        startFlowExecution(input: {{
            flowId: "{etl_flow['id']}"
            flowVersion: 1
        }}) {{ id flowId events {{ eventType }} }}
    }}
    """)
    fe = data["startFlowExecution"]
    fe_id = fe["id"]
    print(f"  ✔ Flow execution created: {fe_id}")

    for event in [
        {
            "eventType": "started",
            "metadata": {"triggeredBy": "cron", "schedule": "0 2 * * *"},
        },
        {
            "eventType": "progress",
            "payload": {
                "completedNodes": 2,
                "totalNodes": 3,
                "currentNode": "notify_done",
            },
        },
        {
            "eventType": "completed",
            "payload": {"totalDurationSeconds": 120, "nodesCompleted": 3},
        },
    ]:
        _emit_event(fe_id, event)

    # ── 5e. Contract execution (ML Release) ──
    print("\n  ── 5e. Contract execution (ML Release) ──")

    data = gql(f"""
    mutation {{
        startContractExecution(input: {{
            contractId: "{ml_contract['id']}"
            contractVersion: 1
        }}) {{ id contractId events {{ eventType }} }}
    }}
    """)
    ce = data["startContractExecution"]
    ce_id = ce["id"]
    print(f"  ✔ Contract execution created: {ce_id}")

    for event in [
        {
            "eventType": "started",
            "metadata": {"release": "v2.3.0", "initiator": "ci-pipeline"},
        },
        {
            "eventType": "progress",
            "payload": {"phase": "training", "flowsCompleted": 0, "flowsTotal": 2},
        },
        {
            "eventType": "progress",
            "payload": {"phase": "assessment", "flowsCompleted": 1, "flowsTotal": 2},
        },
        {
            "eventType": "outcome_produced",
            "payload": {
                "accuracy": 0.93,
                "f1": 0.89,
                "deploymentUrl": "https://models.example.com/v2.3.0",
                "allOutcomesMet": True,
            },
        },
        {
            "eventType": "completed",
            "metadata": {"approvedBy": "lead-ds", "totalDurationMinutes": 47},
        },
    ]:
        _emit_event(ce_id, event)

    # ── 5f. Block execution within a flow ──
    print("\n  ── 5f. Block execution within flow ──")

    ml_nodes = ml_flow.get("nodes", [])
    ml_node_ref = ml_nodes[2]["id"] if len(ml_nodes) > 2 else "00000000-0000-0000-0000-000000000010"

    data = gql(f"""
    mutation {{
        startBlockExecution(input: {{
            nodeReferenceId: "{ml_node_ref}"
            workBlockId: "{train_id}"
            workBlockVersion: 1
            flowExecutionId: "{fe_id}"
            executorType: "system"
            executorId: "gpu-worker-12"
        }}) {{ id state }}
    }}
    """)
    nested_be_id = data["startBlockExecution"]["id"]
    print(f"  ✔ Block execution {nested_be_id} linked to flow {fe_id}")

    for event in [
        {"eventType": "started"},
        {
            "eventType": "progress",
            "payload": {"epoch": 5, "totalEpochs": 20, "trainLoss": 0.34},
        },
        {
            "eventType": "progress",
            "payload": {
                "epoch": 20,
                "totalEpochs": 20,
                "trainLoss": 0.08,
                "valLoss": 0.12,
            },
        },
        {
            "eventType": "outcome_produced",
            "payload": {"accuracy": 0.93, "f1": 0.89, "modelSize": "142MB"},
        },
        {"eventType": "completed"},
    ]:
        _emit_event(nested_be_id, event)
    print("  ✔ Events: started → progress(5/20) → progress(20/20) → outcome → completed")

    # ── 5g. Skipped block execution ──
    print("\n  ── 5g. Skipped block execution ──")

    data = gql(f"""
    mutation {{
        startBlockExecution(input: {{
            nodeReferenceId: "{etl_node_ids.get('notify_done', '00000000-0000-0000-0000-000000000004')}"
            workBlockId: "{notify_id}"
            workBlockVersion: 1
            executorType: "system"
            executorId: "orchestrator"
        }}) {{ id state }}
    }}
    """)
    skipped_be_id = data["startBlockExecution"]["id"]

    _emit_event(skipped_be_id, {
        "eventType": "skipped",
        "payload": {"reason": "Notification suppressed: dry-run mode"},
        "metadata": {"dryRun": True},
    })
    print(f"  ✔ Block {skipped_be_id}: created → skipped (dry-run)")


def _emit_event(execution_id: str, event: dict) -> None:
    """Helper to emit a single execution event via GraphQL."""
    parts = [f'executionId: "{execution_id}"']
    parts.append(f'eventType: "{event["eventType"]}"')

    if event.get("executorType"):
        parts.append(f'executorType: "{event["executorType"]}"')
    if event.get("executorId"):
        parts.append(f'executorId: "{event["executorId"]}"')
    if event.get("payload") is not None:
        parts.append(f"payload: {to_gql_value(event['payload'])}")
    if event.get("metadata") is not None:
        parts.append(f"metadata: {to_gql_value(event['metadata'])}")

    mutation = f"""
    mutation {{
        emitExecutionEvent(input: {{ {', '.join(parts)} }}) {{
            id eventType
        }}
    }}
    """
    data = gql(mutation)
    evt = data["emitExecutionEvent"]
    print(f"    → {evt['eventType']}")


# ---------------------------------------------------------------------------
# 6. Verification queries
# ---------------------------------------------------------------------------


def verify_seed() -> None:
    heading("6 · Verification Queries")

    data = gql("""
    query {
        workBlocks(latestOnly: true) { id name version }
    }
    """)
    wbs = data["workBlocks"]
    print(f"  Work blocks (latest versions): {len(wbs)}")
    for wb in wbs:
        print(f"    • {wb['name']} v{wb['version']}")

    data = gql("""
    query {
        flows(latestOnly: true) { id name version }
    }
    """)
    fs = data["flows"]
    print(f"\n  Flows (latest versions): {len(fs)}")
    for f in fs:
        print(f"    • {f['name']} v{f['version']}")

    data = gql("""
    query {
        contracts(latestOnly: true) { id name version }
    }
    """)
    cs = data["contracts"]
    print(f"\n  Contracts (latest versions): {len(cs)}")
    for c in cs:
        print(f"    • {c['name']} v{c['version']}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed OpenOMA database via GraphQL API"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000/graphql",
        help="GraphQL endpoint URL (default: http://localhost:8000/graphql)",
    )
    args = parser.parse_args()

    global API_URL
    API_URL = args.url

    print(f"🌱 OpenOMA Seed Script — targeting {API_URL}")

    blocks = create_work_blocks()
    blocks = create_versioned_updates(blocks)
    flows = create_flows(blocks)
    contracts = create_contracts(flows)
    create_executions(blocks, flows, contracts)
    verify_seed()

    print(f"\n{'='*60}")
    print("  ✅ Seed complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
