// src/shared/components/DetailField.jsx
import React from "react";

/**
 * Display field with uppercase label and value.
 * Used for read-only detail views like BookDetailPage.
 */
export function DetailField({ label, children, className = "" }) {
  return (
    <div className={className}>
      <div className="text-xs font-semibold uppercase text-slate-500">{label}</div>
      <div className="text-slate-900">{children != null && children !== "" ? children : "—"}</div>
    </div>
  );
}

export default DetailField;
