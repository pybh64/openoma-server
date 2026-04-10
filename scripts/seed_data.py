#!/usr/bin/env python3
"""Seed the database with sample data for development.

Usage:
    uv run python scripts/seed_data.py
"""

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from openoma_server.database import close_db, init_db
from openoma_server.models.contract import ContractDoc, RequiredOutcomeDoc
from openoma_server.models.embedded import (
    EdgeDoc,
    ExpectedOutcomeDoc,
    FlowReferenceDoc,
    NodeReferenceDoc,
    PortDescriptorDoc,
)
from openoma_server.models.flow import FlowDoc
from openoma_server.models.work_block import WorkBlockDoc

# Stable UUIDs for reproducibility
WB_REVIEW = uuid4()
WB_APPROVE = uuid4()
WB_NOTIFY = uuid4()
FLOW_APPROVAL = uuid4()
OUTCOME_QUALITY = uuid4()
CONTRACT_MAIN = uuid4()


async def seed():
    await init_db()
    print("🌱 Seeding database...")

    # ── Work Blocks ─────────────────────────────────────────
    blocks = [
        WorkBlockDoc(
            entity_id=WB_REVIEW,
            version=1,
            name="Document Review",
            description="Review the submitted document for completeness and accuracy",
            created_at=datetime.now(UTC),
            created_by="seed",
            inputs=[
                PortDescriptorDoc(name="document", schema_def={"type": "object"}),
            ],
            outputs=[
                PortDescriptorDoc(name="review_result", schema_def={"type": "string"}),
            ],
            execution_hints=["manual", "requires-expertise"],
            expected_outcome=ExpectedOutcomeDoc(
                description="Document reviewed with clear accept/reject decision",
            ),
            metadata={"category": "review", "estimated_minutes": 30},
        ),
        WorkBlockDoc(
            entity_id=WB_APPROVE,
            version=1,
            name="Manager Approval",
            description="Manager reviews and approves or rejects the item",
            created_at=datetime.now(UTC),
            created_by="seed",
            inputs=[
                PortDescriptorDoc(name="item", schema_def={"type": "object"}),
                PortDescriptorDoc(name="review_result", schema_def={"type": "string"}),
            ],
            outputs=[
                PortDescriptorDoc(name="decision", schema_def={"type": "string"}),
            ],
            execution_hints=["manual", "manager-only"],
            metadata={"category": "approval"},
        ),
        WorkBlockDoc(
            entity_id=WB_NOTIFY,
            version=1,
            name="Send Notification",
            description="Send email notification about the decision",
            created_at=datetime.now(UTC),
            created_by="seed",
            inputs=[
                PortDescriptorDoc(name="decision", schema_def={"type": "string"}),
                PortDescriptorDoc(name="recipients", schema_def={"type": "array"}),
            ],
            outputs=[],
            execution_hints=["automated", "async"],
            metadata={"category": "notification"},
        ),
    ]

    for b in blocks:
        await b.insert()
    print(f"  ✅ Created {len(blocks)} work blocks")

    # ── Flow ────────────────────────────────────────────────
    node_review = uuid4()
    node_approve = uuid4()
    node_notify = uuid4()

    flow = FlowDoc(
        entity_id=FLOW_APPROVAL,
        version=1,
        name="Document Approval Flow",
        description="Review → Approve → Notify workflow for documents",
        created_at=datetime.now(UTC),
        created_by="seed",
        nodes=[
            NodeReferenceDoc(
                id=node_review,
                target_id=WB_REVIEW,
                target_version=1,
                alias="review",
                metadata={"position": {"x": 100, "y": 200}},
            ),
            NodeReferenceDoc(
                id=node_approve,
                target_id=WB_APPROVE,
                target_version=1,
                alias="approve",
                metadata={"position": {"x": 400, "y": 200}},
            ),
            NodeReferenceDoc(
                id=node_notify,
                target_id=WB_NOTIFY,
                target_version=1,
                alias="notify",
                metadata={"position": {"x": 700, "y": 200}},
            ),
        ],
        edges=[
            EdgeDoc(
                source_id=node_review,
                target_id=node_approve,
            ),
            EdgeDoc(
                source_id=node_approve,
                target_id=node_notify,
            ),
        ],
        metadata={"canvas_zoom": 1.0, "canvas_offset": {"x": 0, "y": 0}},
    )
    await flow.insert()
    print("  ✅ Created 1 flow (Document Approval)")

    # ── Required Outcome ────────────────────────────────────
    outcome = RequiredOutcomeDoc(
        entity_id=OUTCOME_QUALITY,
        version=1,
        name="Quality Check Passed",
        description="All documents pass quality review with no critical issues",
        created_at=datetime.now(UTC),
        created_by="seed",
        assessment_bindings=[],
        metadata={},
    )
    await outcome.insert()
    print("  ✅ Created 1 required outcome")

    # ── Contract ────────────────────────────────────────────
    contract = ContractDoc(
        entity_id=CONTRACT_MAIN,
        version=1,
        name="Document Processing Contract",
        description="End-to-end document processing with review, approval, and notification",
        created_at=datetime.now(UTC),
        created_by="seed",
        owners=[],
        work_flows=[
            FlowReferenceDoc(flow_id=FLOW_APPROVAL, flow_version=1),
        ],
        sub_contracts=[],
        required_outcomes=[],
        metadata={"priority": "high"},
    )
    await contract.insert()
    print("  ✅ Created 1 contract")

    print("\n🎉 Seeding complete!")
    print(f"   Work Blocks: {WB_REVIEW}, {WB_APPROVE}, {WB_NOTIFY}")
    print(f"   Flow:        {FLOW_APPROVAL}")
    print(f"   Outcome:     {OUTCOME_QUALITY}")
    print(f"   Contract:    {CONTRACT_MAIN}")

    await close_db()


if __name__ == "__main__":
    asyncio.run(seed())
