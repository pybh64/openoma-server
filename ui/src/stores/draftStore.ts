import { create } from "zustand";
import type { FlowDraft, NodePositionData } from "@/types";

interface DraftState {
  draft: FlowDraft | null;
  isDirty: boolean;
  selectedNodeId: string | null;
  selectedEdge: { sourceId: string | null; targetId: string } | null;

  setDraft: (draft: FlowDraft | null) => void;
  markDirty: () => void;
  markClean: () => void;
  selectNode: (nodeId: string | null) => void;
  selectEdge: (edge: { sourceId: string | null; targetId: string } | null) => void;
  updatePositions: (positions: NodePositionData[]) => void;
}

function getNodePositionId(position: NodePositionData & { node_reference_id?: string }): string {
  return position.nodeReferenceId ?? position.node_reference_id ?? "";
}

export const useDraftStore = create<DraftState>((set) => ({
  draft: null,
  isDirty: false,
  selectedNodeId: null,
  selectedEdge: null,

  setDraft: (draft) =>
    set((state) => {
      if (!draft) {
        return { draft: null, isDirty: false, selectedNodeId: null, selectedEdge: null };
      }

      const selectedNodeId =
        state.selectedNodeId && draft.nodes.some((node) => node.id === state.selectedNodeId)
          ? state.selectedNodeId
          : null;

      const selectedEdge =
        !selectedNodeId &&
          state.selectedEdge &&
          draft.edges.some(
            (edge) =>
              edge.sourceId === state.selectedEdge?.sourceId &&
              edge.targetId === state.selectedEdge?.targetId,
          )
          ? state.selectedEdge
          : null;

      return { draft, isDirty: false, selectedNodeId, selectedEdge };
    }),
  markDirty: () => set({ isDirty: true }),
  markClean: () => set({ isDirty: false }),
  selectNode: (nodeId) => set({ selectedNodeId: nodeId, selectedEdge: null }),
  selectEdge: (edge) => edge
    ? set({ selectedEdge: edge, selectedNodeId: null })
    : set({ selectedEdge: null }),
  updatePositions: (positions) =>
    set((state) => {
      if (!state.draft) return {};

      const normalizedPositions = state.draft.nodePositions
        .map((np) => ({
          ...np,
          nodeReferenceId: getNodePositionId(np as NodePositionData & { node_reference_id?: string }),
        }))
        .filter((np) => np.nodeReferenceId);
      const posMap = new Map(positions.map((p) => [p.nodeReferenceId, p]));
      const updated = normalizedPositions.map((np) => {
        const u = posMap.get(np.nodeReferenceId);
        return u ? { ...np, ...u } : np;
      });
      // Add any new positions
      for (const p of positions) {
        if (!updated.find((np) => np.nodeReferenceId === p.nodeReferenceId)) {
          updated.push(p);
        }
      }
      return { draft: { ...state.draft, nodePositions: updated }, isDirty: true };
    }),
}));
