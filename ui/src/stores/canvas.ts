import type { Node, Edge } from "@xyflow/react";
import { create } from "zustand";

interface CanvasSnapshot {
  nodes: Node[];
  edges: Edge[];
}

interface CanvasState {
  nodes: Node[];
  edges: Edge[];
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
  undoStack: CanvasSnapshot[];
  redoStack: CanvasSnapshot[];

  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  setSelectedNodeId: (id: string | null) => void;
  setSelectedEdgeId: (id: string | null) => void;
  pushSnapshot: () => void;
  undo: () => void;
  redo: () => void;
  reset: () => void;
}

const MAX_UNDO = 50;

export const useCanvasStore = create<CanvasState>()((set, get) => ({
  nodes: [],
  edges: [],
  selectedNodeId: null,
  selectedEdgeId: null,
  undoStack: [],
  redoStack: [],

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  setSelectedNodeId: (id) => set({ selectedNodeId: id, selectedEdgeId: null }),
  setSelectedEdgeId: (id) => set({ selectedEdgeId: id, selectedNodeId: null }),

  pushSnapshot: () => {
    const { nodes, edges, undoStack } = get();
    const snapshot = { nodes: structuredClone(nodes), edges: structuredClone(edges) };
    set({
      undoStack: [...undoStack.slice(-MAX_UNDO + 1), snapshot],
      redoStack: [],
    });
  },

  undo: () => {
    const { nodes, edges, undoStack, redoStack } = get();
    if (undoStack.length === 0) return;
    const prev = undoStack[undoStack.length - 1]!;
    set({
      nodes: prev.nodes,
      edges: prev.edges,
      undoStack: undoStack.slice(0, -1),
      redoStack: [...redoStack, { nodes: structuredClone(nodes), edges: structuredClone(edges) }],
    });
  },

  redo: () => {
    const { nodes, edges, undoStack, redoStack } = get();
    if (redoStack.length === 0) return;
    const next = redoStack[redoStack.length - 1]!;
    set({
      nodes: next.nodes,
      edges: next.edges,
      redoStack: redoStack.slice(0, -1),
      undoStack: [...undoStack, { nodes: structuredClone(nodes), edges: structuredClone(edges) }],
    });
  },

  reset: () =>
    set({
      nodes: [],
      edges: [],
      selectedNodeId: null,
      selectedEdgeId: null,
      undoStack: [],
      redoStack: [],
    }),
}));
