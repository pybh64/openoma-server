import { create } from "zustand";

interface CanvasState {
  showMinimap: boolean;
  showGrid: boolean;
  snapToGrid: boolean;
  gridSize: number;
  searchPanelOpen: boolean;
  detailPanelOpen: boolean;

  toggleMinimap: () => void;
  toggleGrid: () => void;
  toggleSnap: () => void;
  setSearchPanelOpen: (open: boolean) => void;
  setDetailPanelOpen: (open: boolean) => void;
}

export const useCanvasStore = create<CanvasState>((set) => ({
  showMinimap: true,
  showGrid: true,
  snapToGrid: true,
  gridSize: 20,
  searchPanelOpen: false,
  detailPanelOpen: false,

  toggleMinimap: () => set((s) => ({ showMinimap: !s.showMinimap })),
  toggleGrid: () => set((s) => ({ showGrid: !s.showGrid })),
  toggleSnap: () => set((s) => ({ snapToGrid: !s.snapToGrid })),
  setSearchPanelOpen: (open) => set({ searchPanelOpen: open }),
  setDetailPanelOpen: (open) => set({ detailPanelOpen: open }),
}));
