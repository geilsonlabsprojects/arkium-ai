import { Navigate } from "react-router-dom";
import type { ReactNode } from "react";
import { useAuth } from "../hooks/useAuth";
import Skeleton from "./Skeleton";

/** Bloqueia rotas privadas ate a sessao ser resolvida. */
export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8"><Skeleton className="h-40 w-full" /></div>;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
