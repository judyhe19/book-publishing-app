import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Spinner } from "../../../shared/components/Spinner";

export function RequireAuth({ children }) {
  const { user, loading } = useAuth();
  const loc = useLocation();

  if (loading) {
    return (
      <div className="min-h-[50vh] grid place-items-center">
        <Spinner />
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname }} />;
  return children;
}