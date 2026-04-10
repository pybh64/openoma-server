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

export const useDraftStore = create<DraftState>((set) => ({
  draft: null,
  isDirty: false,
  selectedNodeId: null,
  selectedEdge: null,

  setDraft: (draft) => set({ draft, isDirty: false, selectedNodeId: null, selectedEdge: null }),
  markDirty: () => set({ isDirty: true }),
  markClean: () => set({ isDirty: false }),
  selectNode: (nodeId) => set({ selectedNodeId: nodeId, selectedEdge: null }),
  selectEdge: (edge) => set({ selectedEdge: edge, selectedNodeId: null }),
  updatePositions: (positions) =>
    set((state) => {
      if (!state.draft) return {};
      const posMap = new Map(positions.map((p) => [p.nodeReferenceId, p]));
      const updated = state.draft.nodePositions.map((np) => {
        const u = posMap.get(np.nodeReferenceId);
        return u ? { ...np, ...u } : np;
      });
      // Add any new positions
      for (const p of positions) {
        if (!state.draft.nodePositions.find((np) => np.nodeReferenceId === p.nodeReferenceId)) {
          updated.push(p);
        }
      }
      return { draft: { ...state.draft, nodePositions: updated }, isDirty: true };
    }),
}));
