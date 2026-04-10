import { useMemo, useCallback, useRef } from "react";
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
  type OnNodesChange,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { WorkBlockNode, type WorkBlockNodeData } from "./nodes/WorkBlockNode";
import { EntryNode } from "./nodes/EntryNode";
import { ConditionalEdge } from "./edges/ConditionalEdge";
import { useCanvasStore } from "@/stores/canvasStore";
import type { FlowDraft, NodePositionData } from "@/types";

const nodeTypes: NodeTypes = {
  workBlock: WorkBlockNode as unknown as NodeTypes["workBlock"],
  entry: EntryNode as unknown as NodeTypes["entry"],
};

const edgeTypes: EdgeTypes = {
  conditional: ConditionalEdge as unknown as EdgeTypes["conditional"],
};

interface DraftCanvasProps {
  draft: FlowDraft;
  onConnect: (source: string, target: string) => void;
  onNodeSelect: (nodeRefId: string | null) => void;
  onNodesPositionChange: (positions: NodePositionData[]) => void;
}

export function DraftCanvas({
  draft,
  onConnect,
  onNodeSelect,
  onNodesPositionChange,
}: DraftCanvasProps) {
  const { showMinimap, showGrid } = useCanvasStore();
  const dragTimeoutRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  const { initialNodes, initialEdges } = useMemo(() => {
    return buildDraftReactFlowData(draft);
  }, [draft]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  const handleNodesChange: OnNodesChange = useCallback(
    (changes: NodeChange[]) => {
      onNodesChange(changes);

      // Debounce position updates
      const posChanges = changes.filter(
        (c) => c.type === "position" && (c as { dragging?: boolean }).dragging === false
      );
      if (posChanges.length > 0) {
        clearTimeout(dragTimeoutRef.current);
        dragTimeoutRef.current = setTimeout(() => {
          // Get current node positions
          setNodes((nds) => {
            const positions: NodePositionData[] = nds
              .filter((n) => n.id !== "__entry__")
              .map((n) => ({
                nodeReferenceId: n.id,
                x: n.position.x,
                y: n.position.y,
              }));
            onNodesPositionChange(positions);
            return nds;
          });
        }, 300);
      }
    },
    [onNodesChange, onNodesPositionChange, setNodes]
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

  const handleSelectionChange = useCallback(
    ({ nodes: selected }: OnSelectionChangeParams) => {
      if (selected.length === 1 && selected[0].id !== "__entry__") {
        onNodeSelect(selected[0].id);
      } else {
        onNodeSelect(null);
      }
    },
    [onNodeSelect]
  );

  const handlePaneClick = useCallback(() => {
    onNodeSelect(null);
  }, [onNodeSelect]);

  const defaultViewport = draft.viewport
    ? { x: draft.viewport.x, y: draft.viewport.y, zoom: draft.viewport.zoom }
    : { x: 100, y: 100, zoom: 0.85 };

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={handleNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={handleConnect}
      onSelectionChange={handleSelectionChange}
      onPaneClick={handlePaneClick}
      nodeTypes={nodeTypes}
      edgeTypes={edgeTypes}
      defaultViewport={defaultViewport}
      fitView={!draft.viewport}
      fitViewOptions={{ padding: 0.2 }}
      nodesDraggable
      nodesConnectable
      elementsSelectable
      selectNodesOnDrag={false}
      snapToGrid
      snapGrid={[20, 20]}
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

function buildDraftReactFlowData(draft: FlowDraft): {
  initialNodes: Node[];
  initialEdges: RFEdge[];
} {
  const posMap = new Map<string, { x: number; y: number }>();
  if (draft.nodePositions) {
    for (const np of draft.nodePositions) {
      const nri = (np as any).nodeReferenceId ?? (np as any).node_reference_id;
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
      draggable: true,
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

  const rfEdges: RFEdge[] = draft.edges.map((e, idx) => ({
    id: `e-${e.sourceId ?? "entry"}-${e.targetId}-${idx}`,
    source: e.sourceId ?? "__entry__",
    target: e.targetId,
    type: e.condition ? "conditional" : "default",
    data: e.condition ? { conditionDescription: e.condition.description } : undefined,
  }));

  return { initialNodes: nodes, initialEdges: rfEdges };
}
