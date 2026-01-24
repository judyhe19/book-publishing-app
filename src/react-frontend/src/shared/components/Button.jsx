import React from "react";

export function Button({ children, variant = "primary", className = "", ...props }) {
  const base =
    "inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-medium transition";
  const styles =
    variant === "primary"
      ? "bg-slate-900 text-white hover:bg-slate-800 disabled:opacity-60"
      : "border border-slate-200 text-slate-900 hover:bg-slate-50 disabled:opacity-60";

  return (
    <button {...props} className={[base, styles, className].join(" ")}>
      {children}
    </button>
  );
}