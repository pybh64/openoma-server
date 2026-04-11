import { useMemo, useCallback, useEffect, useState } from "react";
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
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { WorkBlockNode, type WorkBlockNodeData } from "./nodes/WorkBlockNode";
import { EntryNode } from "./nodes/EntryNode";
import { FlowEdge } from "./edges/FlowEdge";
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
  flow: FlowEdge as unknown as EdgeTypes["flow"],
};

interface FlowCanvasProps {
  flow: Flow;
  layout: CanvasLayout | null;
  workBlockSummaries?: WorkBlockSummary[];
  nodeStates?: NodeExecutionState[];
  onNodeSelect?: (nodeRefId: string | null) => void;
  onEdgeSelect?: (edge: { sourceId: string | null; targetId: string } | null) => void;
  selectedEdge?: { sourceId: string | null; targetId: string } | null;
  readOnly?: boolean;
}

export function FlowCanvas({
  flow,
  layout,
  workBlockSummaries,
  nodeStates,
  onNodeSelect,
  onEdgeSelect,
  selectedEdge,
  readOnly = true,
}: FlowCanvasProps) {
  const { showMinimap, showGrid } = useCanvasStore();
  const [fitViewOnInit, setFitViewOnInit] = useState(() => !layout?.viewport);

  const { initialNodes, initialEdges } = useMemo(() => {
    return buildReactFlowData(flow, layout, workBlockSummaries, nodeStates, selectedEdge);
  }, [flow, layout, workBlockSummaries, nodeStates, selectedEdge]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => {
    setNodes(initialNodes);
  }, [initialNodes, setNodes]);

  useEffect(() => {
    setEdges(initialEdges);
  }, [initialEdges, setEdges]);

  const handleSelectionChange = useCallback(
    ({ nodes: selectedNodes, edges: selectedEdges }: OnSelectionChangeParams) => {
      if (selectedNodes.length === 1) {
        onNodeSelect?.(selectedNodes[0].id);
        onEdgeSelect?.(null);
      } else if (selectedEdges.length === 1) {
        onNodeSelect?.(null);
        onEdgeSelect?.({
          sourceId: selectedEdges[0].source === "__entry__" ? null : selectedEdges[0].source,
          targetId: selectedEdges[0].target,
        });
      } else {
        onNodeSelect?.(null);
        onEdgeSelect?.(null);
      }
    },
    [onEdgeSelect, onNodeSelect]
  );

  const handlePaneClick = useCallback(() => {
    onNodeSelect?.(null);
    onEdgeSelect?.(null);
  }, [onEdgeSelect, onNodeSelect]);

  const handleNodeClick = useCallback(
    (_event: unknown, node: Node) => {
      if (node.id === "__entry__") {
        onNodeSelect?.(null);
        return;
      }
      onNodeSelect?.(node.id);
      onEdgeSelect?.(null);
    },
    [onEdgeSelect, onNodeSelect]
  );

  const handleEdgeClick = useCallback(
    (_event: unknown, edge: RFEdge) => {
      onNodeSelect?.(null);
      onEdgeSelect?.({
        sourceId: edge.source === "__entry__" ? null : edge.source,
        targetId: edge.target,
      });
    },
    [onEdgeSelect, onNodeSelect]
  );

  const defaultViewport = layout?.viewport
    ? { x: layout.viewport.x, y: layout.viewport.y, zoom: layout.viewport.zoom }
    : { x: 100, y: 100, zoom: 0.85 };

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={readOnly ? undefined : onNodesChange}
      onEdgesChange={onEdgesChange}
      onNodeClick={handleNodeClick}
      onEdgeClick={handleEdgeClick}
      onSelectionChange={handleSelectionChange}
      onPaneClick={handlePaneClick}
      onInit={() => setFitViewOnInit(false)}
      nodeTypes={nodeTypes}
      edgeTypes={edgeTypes}
      defaultViewport={defaultViewport}
      fitView={fitViewOnInit}
      fitViewOptions={{ padding: 0.2 }}
      nodesDraggable={!readOnly}
      nodesConnectable={false}
      edgesFocusable
      elementsSelectable
      selectNodesOnDrag={false}
      selectionOnDrag={false}
      elevateEdgesOnSelect
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
  nodeStates?: NodeExecutionState[],
  selectedEdge?: { sourceId: string | null; targetId: string } | null
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
      inputCount: nodeRef.workBlock?.inputs?.length ?? 0,
      outputCount: nodeRef.workBlock?.outputs?.length ?? 0,
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
    type: "flow",
    selected:
      selectedEdge?.sourceId === e.sourceId &&
      selectedEdge?.targetId === e.targetId,
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color:
        selectedEdge?.sourceId === e.sourceId &&
        selectedEdge?.targetId === e.targetId
          ? "var(--color-primary)"
          : "var(--color-muted-foreground)",
    },
    data: {
      conditionDescription: e.condition?.description,
      portMappings: e.portMappings,
    },
    animated: stateMap.get(e.targetId)?.state === "in_progress",
  }));

  return { initialNodes: nodes, initialEdges: rfEdges };
}
