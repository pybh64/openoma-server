import { useCallback, useRef, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  type Connection,
  type Node,
  type Edge,
  type OnConnect,
  BackgroundVariant,
  type ReactFlowInstance,
} from "@xyflow/react";
import { v4 as uuid } from "uuid";
import { WorkBlockNode } from "./nodes/WorkBlockNode";
import { ConditionalEdge } from "./edges/ConditionalEdge";
import { useCanvasStore } from "@/stores/canvas";

const nodeTypes = { workBlock: WorkBlockNode };
const edgeTypes = { conditional: ConditionalEdge };

interface FlowCanvasProps {
  onInit?: (instance: ReactFlowInstance) => void;
}

export function FlowCanvas({ onInit }: FlowCanvasProps) {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const store = useCanvasStore();

  const [nodes, setNodes, onNodesChange] = useNodesState(store.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(store.edges);

  // Sync to zustand store on change
  const syncNodes = useCallback(
    (changes: any) => {
      onNodesChange(changes);
      // defer sync to next tick to get the updated nodes
      requestAnimationFrame(() => {
        store.setNodes(nodes);
      });
    },
    [onNodesChange, store, nodes]
  );

  const syncEdges = useCallback(
    (changes: any) => {
      onEdgesChange(changes);
      requestAnimationFrame(() => {
        store.setEdges(edges);
      });
    },
    [onEdgesChange, store, edges]
  );

  const onConnect: OnConnect = useCallback(
    (connection: Connection) => {
      store.pushSnapshot();
      const newEdge: Edge = {
        ...connection,
        id: `e-${uuid()}`,
        type: "conditional",
        data: { condition: null, portMappings: [] },
      } as Edge;
      setEdges((eds) => addEdge(newEdge, eds));
    },
    [setEdges, store]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const data = event.dataTransfer.getData("application/openoma-workblock");
      if (!data) return;

      const workBlock = JSON.parse(data);
      const bounds = reactFlowWrapper.current?.getBoundingClientRect();
      if (!bounds) return;

      store.pushSnapshot();

      const nodeId = uuid();
      const newNode: Node = {
        id: nodeId,
        type: "workBlock",
        position: {
          x: event.clientX - bounds.left - 90,
          y: event.clientY - bounds.top - 30,
        },
        data: {
          label: workBlock.name,
          alias: "",
          workBlockId: workBlock.id,
          workBlockVersion: workBlock.version,
          inputs: workBlock.inputs ?? [],
          outputs: workBlock.outputs ?? [],
        },
      };

      setNodes((nds) => [...nds, newNode]);
    },
    [setNodes, store]
  );

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      store.setSelectedNodeId(node.id);
    },
    [store]
  );

  const onEdgeClick = useCallback(
    (_: React.MouseEvent, edge: Edge) => {
      store.setSelectedEdgeId(edge.id);
    },
    [store]
  );

  const onPaneClick = useCallback(() => {
    store.setSelectedNodeId(null);
    store.setSelectedEdgeId(null);
  }, [store]);

  const defaultEdgeOptions = useMemo(
    () => ({
      type: "conditional",
      animated: false,
    }),
    []
  );

  return (
    <div ref={reactFlowWrapper} className="h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={syncNodes}
        onEdgesChange={syncEdges}
        onConnect={onConnect}
        onDragOver={onDragOver}
        onDrop={onDrop}
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        onPaneClick={onPaneClick}
        onInit={onInit}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        defaultEdgeOptions={defaultEdgeOptions}
        fitView
        deleteKeyCode={["Backspace", "Delete"]}
        className="bg-background"
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={16}
          size={1}
          className="!bg-background"
        />
        <Controls className="!bg-card !border-border !shadow-md" />
        <MiniMap
          className="!bg-card !border-border"
          nodeColor="hsl(var(--muted))"
          maskColor="rgba(0,0,0,0.3)"
        />
      </ReactFlow>
    </div>
  );
}
