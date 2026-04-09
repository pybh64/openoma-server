import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
  userId: string | null;
  tenantId: string | null;
  roles: string[];
  isAuthenticated: boolean;
  setAuth: (userId: string, tenantId: string, roles: string[]) => void;
  clearAuth: () => void;
  hasRole: (role: string) => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      userId: null,
      tenantId: null,
      roles: [],
      isAuthenticated: false,
      setAuth: (userId, tenantId, roles) =>
        set({ userId, tenantId, roles, isAuthenticated: true }),
      clearAuth: () =>
        set({ userId: null, tenantId: null, roles: [], isAuthenticated: false }),
      hasRole: (role) => get().roles.includes(role),
    }),
    { name: "openoma-auth" }
  )
);
