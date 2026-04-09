# UI Plan & Progress — OpenOMA

Date: 2026-04-09

Summary

This document captures the current UI implementation progress, recent fixes, and next steps for the OpenOMA frontend (ui/).

Recent progress

- Prefect-style DAG canvas implemented with ELK auto-layout; nodes remain draggable and connectable.
- Fixed edge rendering: use React Flow MarkerType.ArrowClosed and Tailwind v4 CSS variables (var(--color-*)). Arrowheads and strokes now render correctly.
- Simplified node handles (left/right) and improved styling.
- Added Node Inspector panel to FlowEditor (fetches WorkBlock details, delete, navigate).
- Added node hover tooltips (description, input/output counts and names) for both edit and read-only modes.
- Enriched FlowDetail by prefetching WorkBlocks and passing detailed metadata into DAG nodes.
- Fixed Background and MiniMap color rendering issues (use var(--color-*) instead of invalid hsl wrappers).

Next steps

1. Visual QA & polish: spacing, tooltip typography, edge stroke responsiveness across zoom levels.
2. Add tests for canvas → GraphQL serialization and ELK layout snapshot tests.
3. Accessibility audit: keyboard navigation, focus states, and screen-reader labels for canvas elements.
4. Optimize bundle: code-split FlowCanvas heavy modules (ELK + React Flow) to reduce initial chunk size.
5. Final UX: build modal flows for port mapping and condition builder; integrate optimistic updates for save operations.

How to run (dev)

# Start backend
make dev

# Start UI
cd ui && make ui-dev

Notes

- The primary UI work lives in ui/src/components/canvas and ui/src/pages/flows.
- Plan updates should live in ui/plan.md so they are versioned alongside code.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
