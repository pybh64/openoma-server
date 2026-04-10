import { useMemo, useCallback } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge as RFEdge,
  type NodeTypes,
  type EdgeTypes,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  type OnSelectionChangeParams,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { WorkBlockNode, type WorkBlockNodeData } from "./nodes/WorkBlockNode";
import { EntryNode } from "./nodes/EntryNode";
import { ConditionalEdge } from "./edges/ConditionalEdge";
import { useCanvasStore } from "@/stores/canvasStore";
import type {
  Flow,
  CanvasLayout,
  WorkBlockSummary,
  NodeExecutionState,
} from "@/types";

const nodeTypes: NodeTypes = {
  workBlock: WorkBlockNode as unknown as NodeTypes["workBlock"],
  entry: EntryNode as unknown as NodeTypes["entry"],
};

const edgeTypes: EdgeTypes = {
  conditional: ConditionalEdge as unknown as EdgeTypes["conditional"],
};

interface FlowCanvasProps {
  flow: Flow;
  layout: CanvasLayout | null;
  workBlockSummaries?: WorkBlockSummary[];
  nodeStates?: NodeExecutionState[];
  onNodeSelect?: (nodeRefId: string | null) => void;
  readOnly?: boolean;
}

export function FlowCanvas({
  flow,
  layout,
  workBlockSummaries,
  nodeStates,
  onNodeSelect,
  readOnly = true,
}: FlowCanvasProps) {
  const { showMinimap, showGrid } = useCanvasStore();

  const { initialNodes, initialEdges } = useMemo(() => {
    return buildReactFlowData(flow, layout, workBlockSummaries, nodeStates);
  }, [flow, layout, workBlockSummaries, nodeStates]);

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  const handleSelectionChange = useCallback(
    ({ nodes: selectedNodes }: OnSelectionChangeParams) => {
      if (selectedNodes.length === 1) {
        onNodeSelect?.(selectedNodes[0].id);
      } else {
        onNodeSelect?.(null);
      }
    },
    [onNodeSelect]
  );

  const handlePaneClick = useCallback(() => {
    onNodeSelect?.(null);
  }, [onNodeSelect]);

  const defaultViewport = layout?.viewport
    ? { x: layout.viewport.x, y: layout.viewport.y, zoom: layout.viewport.zoom }
    : { x: 100, y: 100, zoom: 0.85 };

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={readOnly ? undefined : onNodesChange}
      onEdgesChange={readOnly ? undefined : onEdgesChange}
      onSelectionChange={handleSelectionChange}
      onPaneClick={handlePaneClick}
      nodeTypes={nodeTypes}
      edgeTypes={edgeTypes}
      defaultViewport={defaultViewport}
      fitView={!layout?.viewport}
      fitViewOptions={{ padding: 0.2 }}
      nodesDraggable={!readOnly}
      nodesConnectable={false}
      elementsSelectable
      selectNodesOnDrag={false}
      proOptions={{ hideAttribution: true }}
    >
      {showGrid && <Background variant={BackgroundVariant.Dots} gap={20} size={1} />}
      <Controls showInteractive={false} />
      {showMinimap && (
        <MiniMap
          nodeStrokeWidth={3}
          pannable
          zoomable
          style={{ width: 150, height: 100 }}
        />
      )}
    </ReactFlow>
  );
}

function buildReactFlowData(
  flow: Flow,
  layout: CanvasLayout | null,
  summaries?: WorkBlockSummary[],
  nodeStates?: NodeExecutionState[]
): { initialNodes: Node[]; initialEdges: RFEdge[] } {
  const posMap = new Map<string, { x: number; y: number; width?: number | null; height?: number | null }>();
  if (layout?.nodePositions) {
    for (const np of layout.nodePositions) {
      posMap.set(np.nodeReferenceId, np);
    }
  }
  const summaryMap = new Map<string, WorkBlockSummary>();
  if (summaries) {
    for (const s of summaries) {
      summaryMap.set(s.id, s);
    }
  }
  const stateMap = new Map<string, NodeExecutionState>();
  if (nodeStates) {
    for (const ns of nodeStates) {
      stateMap.set(ns.nodeReferenceId, ns);
    }
  }

  // Find entry edges (sourceId is null)
  const entryEdges = flow.edges.filter((e) => e.sourceId === null);
  const hasEntryNode = entryEdges.length > 0;

  const nodes: Node[] = [];

  // Add entry node if needed
  if (hasEntryNode) {
    nodes.push({
      id: "__entry__",
      type: "entry",
      position: { x: 0, y: 150 },
      data: { label: "Start" },
    });
  }

  // Add work block nodes
  flow.nodes.forEach((nodeRef, idx) => {
    const wb = nodeRef.workBlock || summaryMap.get(nodeRef.targetId);
    const pos = posMap.get(nodeRef.id);
    const exState = stateMap.get(nodeRef.id);

    const data: WorkBlockNodeData = {
      label: wb?.name || `Block ${idx + 1}`,
      description: wb?.description || "",
      executionHints: wb?.executionHints || [],
      inputCount: (nodeRef.workBlock as any)?.inputs?.length ?? 0,
      outputCount: (nodeRef.workBlock as any)?.outputs?.length ?? 0,
      workBlockId: nodeRef.targetId,
      workBlockVersion: nodeRef.targetVersion,
      alias: nodeRef.alias,
      nodeReferenceId: nodeRef.id,
      executionState: exState?.state ?? null,
    };

    nodes.push({
      id: nodeRef.id,
      type: "workBlock",
      position: pos
        ? { x: pos.x, y: pos.y }
        : { x: 250 + idx * 280, y: 100 + (idx % 3) * 120 },
      data: data as unknown as Record<string, unknown>,
    });
  });

  // Build edges
  const rfEdges: RFEdge[] = flow.edges.map((e, idx) => ({
    id: `e-${e.sourceId ?? "entry"}-${e.targetId}-${idx}`,
    source: e.sourceId ?? "__entry__",
    target: e.targetId,
    type: e.condition ? "conditional" : "default",
    data: e.condition ? { conditionDescription: e.condition.description } : undefined,
    animated: stateMap.get(e.targetId)?.state === "in_progress",
  }));

  return { initialNodes: nodes, initialEdges: rfEdges };
}
