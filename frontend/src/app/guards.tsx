import { ReactElement } from "react";
import { Navigate } from "react-router-dom";

import { useAuthStore } from "../store/authStore";

export function AuthGuard({ children }: { children: ReactElement }) {
  const token = useAuthStore((s) => s.accessToken);
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export function AdminGuard({ children }: { children: ReactElement }) {
  const user = useAuthStore((s) => s.user);
  if (!user || user.role !== "admin") {
    return <Navigate to="/home" replace />;
  }
  return children;
}

export function MutedGuard({ children }: { children: ReactElement }) {
  const user = useAuthStore((s) => s.user);
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (user.status === "muted") {
    return <Navigate to="/home" replace />;
  }
  return children;
}
