import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  MarkerType,
  addEdge,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  type Node,
  type Edge,
  type Connection,
  type OnConnect,
  type ReactFlowInstance,
} from "@xyflow/react";
import ELK from "elkjs/lib/elk.bundled.js";
import { v4 as uuid } from "uuid";
import { DAGNode } from "./nodes/WorkBlockNode";
import { DAGEdge } from "./edges/ConditionalEdge";

const elk = new ELK();
const nodeTypes = { dag: DAGNode };
const edgeTypes = { dag: DAGEdge };

const NODE_WIDTH = 210;
const NODE_HEIGHT = 56;

const ARROW_MARKER = {
  type: MarkerType.ArrowClosed,
  width: 18,
  height: 18,
  color: "var(--color-muted-foreground)",
};

export interface DAGCanvasNode {
  id: string;
  label: string;
  subtitle?: string;
  status?: "idle" | "running" | "completed" | "failed" | "skipped";
  description?: string;
  inputCount?: number;
  outputCount?: number;
  inputs?: string[];
  outputs?: string[];
  /** opaque payload for click handlers */
  meta?: Record<string, unknown>;
}

export interface DAGCanvasEdge {
  id: string;
  source: string;
  target: string;
  condition?: string;
}

interface DAGCanvasProps {
  nodes: DAGCanvasNode[];
  edges: DAGCanvasEdge[];
  /** Called when user drag-connects two nodes on the canvas */
  onConnect?: (sourceId: string, targetId: string) => void;
  onNodeClick?: (nodeId: string) => void;
  onEdgeClick?: (edgeId: string) => void;
  direction?: "RIGHT" | "DOWN";
  interactive?: boolean;
  className?: string;
}

async function computeLayout(
  dagNodes: DAGCanvasNode[],
  dagEdges: DAGCanvasEdge[],
  direction: string
): Promise<Map<string, { x: number; y: number }>> {
  const graph = {
    id: "root",
    layoutOptions: {
      "elk.algorithm": "layered",
      "elk.direction": direction,
      "elk.spacing.nodeNode": "40",
      "elk.layered.spacing.nodeNodeBetweenLayers": "60",
      "elk.edgeRouting": "ORTHOGONAL",
      "elk.layered.mergeEdges": "true",
    },
    children: dagNodes.map((n) => ({
      id: n.id,
      width: NODE_WIDTH,
      height: NODE_HEIGHT,
    })),
    edges: dagEdges.map((e) => ({
      id: e.id,
      sources: [e.source],
      targets: [e.target],
    })),
  };

  const layout = await elk.layout(graph);
  const positions = new Map<string, { x: number; y: number }>();
  for (const child of layout.children ?? []) {
    positions.set(child.id, { x: child.x ?? 0, y: child.y ?? 0 });
  }
  return positions;
}

function toRFNodes(dagNodes: DAGCanvasNode[], positions: Map<string, { x: number; y: number }>): Node[] {
  return dagNodes.map((n, i) => ({
    id: n.id,
    type: "dag",
    position: positions.get(n.id) ?? { x: i * 260, y: 0 },
    data: {
      label: n.label,
      subtitle: n.subtitle,
      status: n.status,
      description: n.description,
      inputCount: n.inputCount,
      outputCount: n.outputCount,
      inputs: n.inputs,
      outputs: n.outputs,
    },
  }));
}

function toRFEdges(dagEdges: DAGCanvasEdge[]): Edge[] {
  return dagEdges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    type: "dag",
    markerEnd: ARROW_MARKER,
    data: e.condition ? { condition: { description: e.condition } } : {},
  }));
}

export function DAGCanvas({
  nodes: dagNodes,
  edges: dagEdges,
  onConnect: onExternalConnect,
  onNodeClick,
  onEdgeClick,
  direction = "RIGHT",
  interactive = true,
  className,
}: DAGCanvasProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const rfRef = useRef<ReactFlowInstance | null>(null);
  const [layoutDone, setLayoutDone] = useState(false);

  // Structural key: changes when node/edge topology changes (not positions)
  const structureKey = useMemo(
    () =>
      dagNodes.map((n) => n.id).sort().join(",") +
      "|" +
      dagEdges.map((e) => `${e.source}->${e.target}`).sort().join(","),
    [dagNodes, dagEdges]
  );

  // Auto-layout when structure changes
  useEffect(() => {
    if (dagNodes.length === 0) {
      setNodes([]);
      setEdges([]);
      setLayoutDone(true);
      return;
    }

    computeLayout(dagNodes, dagEdges, direction).then((positions) => {
      setNodes(toRFNodes(dagNodes, positions));
      setEdges(toRFEdges(dagEdges));
      setLayoutDone(true);
      requestAnimationFrame(() => rfRef.current?.fitView({ padding: 0.15 }));
    });
  }, [structureKey, direction]);

  // Update node data (labels, status) without re-layouting
  useEffect(() => {
    if (!layoutDone) return;
    setNodes((prev) =>
      prev.map((n) => {
        const src = dagNodes.find((d) => d.id === n.id);
        if (!src) return n;
        return {
          ...n,
          data: {
            label: src.label,
            subtitle: src.subtitle,
            status: src.status,
            description: src.description,
            inputCount: src.inputCount,
            outputCount: src.outputCount,
            inputs: src.inputs,
            outputs: src.outputs,
          },
        };
      })
    );
  }, [dagNodes, layoutDone]);

  const handleConnect: OnConnect = useCallback(
    (connection: Connection) => {
      if (!connection.source || !connection.target) return;
      if (onExternalConnect) {
        onExternalConnect(connection.source, connection.target);
      } else {
        const newEdge: Edge = {
          id: `e-${uuid()}`,
          source: connection.source,
          target: connection.target,
          type: "dag",
          markerEnd: ARROW_MARKER,
          data: {},
        };
        setEdges((eds) => addEdge(newEdge, eds));
      }
    },
    [setEdges, onExternalConnect]
  );

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => onNodeClick?.(node.id),
    [onNodeClick]
  );

  const handleEdgeClick = useCallback(
    (_: React.MouseEvent, edge: Edge) => onEdgeClick?.(edge.id),
    [onEdgeClick]
  );

  const defaultEdgeOptions = useMemo(
    () => ({ type: "dag", markerEnd: ARROW_MARKER }),
    []
  );

  return (
    <div className={className ?? "h-full w-full"}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={handleConnect}
        onNodeClick={handleNodeClick}
        onEdgeClick={handleEdgeClick}
        onInit={(instance) => { rfRef.current = instance; }}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        defaultEdgeOptions={defaultEdgeOptions}
        nodesDraggable={interactive}
        nodesConnectable={interactive}
        elementsSelectable
        deleteKeyCode={interactive ? ["Backspace", "Delete"] : []}
        panOnDrag
        zoomOnScroll
        fitView
        fitViewOptions={{ padding: 0.15 }}
        className="bg-background"
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          className="!bg-background"
          color="var(--color-muted-foreground)"
          style={{ opacity: 0.15 }}
        />
        <Controls
          showInteractive={false}
          className="!bg-card !border-border !shadow-md [&>button]:!bg-card [&>button]:!border-border [&>button]:!text-foreground"
        />
        <MiniMap
          className="!bg-card !border-border"
          nodeColor="var(--color-muted-foreground)"
          maskColor="rgba(0,0,0,0.6)"
        />
      </ReactFlow>
    </div>
  );
}
