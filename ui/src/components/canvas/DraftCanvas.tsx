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
  type Connection,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  type OnSelectionChangeParams,
  type NodeChange,
  type EdgeChange,
  type OnNodesChange,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { WorkBlockNode, type WorkBlockNodeData } from "./nodes/WorkBlockNode";
import { EntryNode } from "./nodes/EntryNode";
import { FlowEdge } from "./edges/FlowEdge";
import { useCanvasStore } from "@/stores/canvasStore";
import type { FlowDraft, NodePositionData } from "@/types";

const nodeTypes: NodeTypes = {
  workBlock: WorkBlockNode as unknown as NodeTypes["workBlock"],
  entry: EntryNode as unknown as NodeTypes["entry"],
};

const edgeTypes: EdgeTypes = {
  flow: FlowEdge as unknown as EdgeTypes["flow"],
};

interface DraftCanvasProps {
  draft: FlowDraft;
  onConnect: (source: string, target: string) => void;
  onNodeSelect: (nodeRefId: string | null) => void;
  onEdgeSelect?: (edge: { sourceId: string | null; targetId: string } | null) => void;
  onNodesPositionChange: (positions: NodePositionData[]) => void;
  selectedEdge?: { sourceId: string | null; targetId: string } | null;
}

export function DraftCanvas({
  draft,
  onConnect,
  onNodeSelect,
  onEdgeSelect,
  onNodesPositionChange,
  selectedEdge,
}: DraftCanvasProps) {
  const { showMinimap, showGrid, snapToGrid, gridSize } = useCanvasStore();
  // An empty object `{}` from the server default is truthy but has no valid zoom.
  const hasValidViewport =
    draft.viewport != null && typeof (draft.viewport as { zoom?: unknown }).zoom === "number";
  const [fitViewOnInit, setFitViewOnInit] = useState(() => !hasValidViewport);

  // Compute nodes AND edges together so selection styling stays in sync with draft changes.
  const { initialNodes, initialEdges } = useMemo(() => {
    return buildDraftReactFlowData(draft, selectedEdge);
  }, [draft, selectedEdge]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => {
    setNodes(initialNodes);
  }, [initialNodes, setNodes]);

  useEffect(() => {
    setEdges(initialEdges);
  }, [initialEdges, setEdges]);

  // Block React Flow's built-in Delete/Backspace deletion — removals go through server mutations.
  const handleNodesChange: OnNodesChange = useCallback(
    (changes: NodeChange[]) => {
      const filtered = changes.filter((c) => c.type !== "remove");
      if (filtered.length > 0) onNodesChange(filtered);
    },
    [onNodesChange]
  );

  const handleEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      const filtered = changes.filter((c) => c.type !== "remove");
      if (filtered.length > 0) onEdgesChange(filtered);
    },
    [onEdgesChange]
  );

  const handleNodeDragStart = useCallback(
    (_event: unknown, node: Node) => {
      if (node.id === "__entry__") {
        onNodeSelect(null);
        onEdgeSelect?.(null);
        return;
      }
      onNodeSelect(node.id);
      onEdgeSelect?.(null);
    },
    [onEdgeSelect, onNodeSelect]
  );

  const handleConnect = useCallback(
    (connection: Connection) => {
      if (connection.source && connection.target) {
        onConnect(
          connection.source === "__entry__" ? "" : connection.source,
          connection.target
        );
      }
    },
    [onConnect]
  );

  const handlePaneClick = useCallback(() => {
    onNodeSelect(null);
    onEdgeSelect?.(null);
  }, [onEdgeSelect, onNodeSelect]);

  const handleSelectionChange = useCallback(
    ({ nodes: selectedNodes, edges: selectedEdges }: OnSelectionChangeParams) => {
      const selectedWorkBlockNode = selectedNodes.find((n) => n.id !== "__entry__");
      if (selectedWorkBlockNode) {
        onNodeSelect(selectedWorkBlockNode.id);
        onEdgeSelect?.(null);
      } else if (selectedEdges.length === 1) {
        onNodeSelect(null);
        onEdgeSelect?.({
          sourceId:
            selectedEdges[0].source === "__entry__" ? null : selectedEdges[0].source,
          targetId: selectedEdges[0].target,
        });
      } else {
        onNodeSelect(null);
        onEdgeSelect?.(null);
      }
    },
    [onEdgeSelect, onNodeSelect],
  );

  const handleNodeClick = useCallback(
    (_event: unknown, node: Node) => {
      if (node.id === "__entry__") {
        onNodeSelect(null);
        onEdgeSelect?.(null);
        return;
      }
      onNodeSelect(node.id);
      onEdgeSelect?.(null);
    },
    [onEdgeSelect, onNodeSelect]
  );

  const handleEdgeClick = useCallback(
    (_event: unknown, edge: RFEdge) => {
      onNodeSelect(null);
      onEdgeSelect?.({
        sourceId: edge.source === "__entry__" ? null : edge.source,
        targetId: edge.target,
      });
    },
    [onEdgeSelect, onNodeSelect]
  );

  const handleNodeDragStop = useCallback(
    (_event: unknown, draggedNode: Node) => {
      const positions: NodePositionData[] = nodes
        .filter((currentNode) => currentNode.id !== "__entry__")
        .map((currentNode) => {
          const position =
            currentNode.id === draggedNode.id ? draggedNode.position : currentNode.position;
          return {
            nodeReferenceId: currentNode.id,
            x: position.x,
            y: position.y,
          };
        });
      onNodesPositionChange(positions);
    },
    [nodes, onNodesPositionChange]
  );

  const defaultViewport = hasValidViewport
    ? {
      x: (draft.viewport as { x: number }).x,
      y: (draft.viewport as { y: number }).y,
      zoom: (draft.viewport as { zoom: number }).zoom,
    }
    : { x: 100, y: 100, zoom: 0.85 };

  return (
    // React Flow requires an explicit-height parent container.
    <div className="w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={handleNodesChange}
        onEdgesChange={handleEdgesChange}
        onNodeDragStart={handleNodeDragStart}
        onNodeDragStop={handleNodeDragStop}
        onNodeClick={handleNodeClick}
        onEdgeClick={handleEdgeClick}
        onConnect={handleConnect}
        onSelectionChange={handleSelectionChange}
        onPaneClick={handlePaneClick}
        onInit={() => setFitViewOnInit(false)}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        defaultViewport={defaultViewport}
        fitView={fitViewOnInit}
        fitViewOptions={{ padding: 0.2 }}
        nodesDraggable
        nodesConnectable
        edgesFocusable
        elementsSelectable
        nodeDragThreshold={2}
        selectionOnDrag={false}
        snapToGrid={snapToGrid}
        snapGrid={[gridSize, gridSize]}
        elevateEdgesOnSelect
        // Disable built-in Delete/Backspace key so only server-side deletion is allowed.
        deleteKeyCode={null}
        connectionLineStyle={{ stroke: "var(--color-primary)", strokeWidth: 2 }}
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
    </div>
  );
}

function buildDraftReactFlowData(
  draft: FlowDraft,
  selectedEdge?: { sourceId: string | null; targetId: string } | null,
): {
  initialNodes: Node[];
  initialEdges: RFEdge[];
} {
  const posMap = new Map<string, { x: number; y: number }>();
  if (draft.nodePositions) {
    for (const np of draft.nodePositions) {
      const nri = getNodePositionId(np);
      if (nri) posMap.set(nri, { x: np.x, y: np.y });
    }
  }

  const entryEdges = draft.edges.filter((e) => e.sourceId === null);
  const hasEntry = entryEdges.length > 0;

  const nodes: Node[] = [];
  if (hasEntry) {
    nodes.push({
      id: "__entry__",
      type: "entry",
      position: { x: 0, y: 150 },
      data: { label: "Start" },
      draggable: false,
    });
  }

  draft.nodes.forEach((nodeRef, idx) => {
    const wb = nodeRef.workBlock;
    const pos = posMap.get(nodeRef.id);

    const data: WorkBlockNodeData = {
      label: wb?.name || `Block ${idx + 1}`,
      description: wb?.description || "",
      executionHints: wb?.executionHints || [],
      inputCount: wb?.inputs?.length ?? 0,
      outputCount: wb?.outputs?.length ?? 0,
      workBlockId: nodeRef.targetId,
      workBlockVersion: nodeRef.targetVersion,
      alias: nodeRef.alias,
      nodeReferenceId: nodeRef.id,
    };

    nodes.push({
      id: nodeRef.id,
      type: "workBlock",
      position: pos || { x: 250 + idx * 280, y: 100 + (idx % 3) * 120 },
      data: data as unknown as Record<string, unknown>,
    });
  });

  const rfEdges: RFEdge[] = draft.edges.map((e, idx) => {
    const sourceId = e.sourceId ?? null;
    const isSelected =
      selectedEdge != null &&
      selectedEdge.sourceId === sourceId &&
      selectedEdge.targetId === e.targetId;
    return {
      id: `e-${e.sourceId ?? "entry"}-${e.targetId}-${idx}`,
      source: e.sourceId ?? "__entry__",
      target: e.targetId,
      type: "flow",
      selected: isSelected,
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: isSelected ? "var(--color-primary)" : "var(--color-muted-foreground)",
      },
      data: {
        conditionDescription: e.condition?.description,
        portMappings: e.portMappings,
      },
    };
  });

  return { initialNodes: nodes, initialEdges: rfEdges };
}

function getNodePositionId(position: NodePositionData & { node_reference_id?: string }): string {
  return position.nodeReferenceId ?? position.node_reference_id ?? "";
}
