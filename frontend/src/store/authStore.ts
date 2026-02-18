import { create } from "zustand";
import { persist } from "zustand/middleware";

type AuthUser = {
  user_id: string;
  username: string;
  role: "user" | "admin";
  status: "active" | "muted" | "banned" | "pending";
};

type AuthState = {
  accessToken: string | null;
  refreshToken: string | null;
  user: AuthUser | null;
  pendingUserId: string | null;
  setSession: (payload: { accessToken: string; refreshToken: string; user: AuthUser }) => void;
  setPendingUserId: (userId: string | null) => void;
  logout: () => void;
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      pendingUserId: null,
      setSession: ({ accessToken, refreshToken, user }) =>
        set({ accessToken, refreshToken, user, pendingUserId: null }),
      setPendingUserId: (pendingUserId) => set({ pendingUserId }),
      logout: () => set({ accessToken: null, refreshToken: null, user: null }),
    }),
    {
      name: "mindedu-auth",
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        pendingUserId: state.pendingUserId,
      }),
    }
  )
);
