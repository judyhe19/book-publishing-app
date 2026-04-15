// src/shared/components/Button.jsx
import React from "react";
import { Link } from "react-router-dom";

export function Button({ children, variant = "primary", className = "", to, state, ...props }) {
  const base =
    "inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-medium transition";
  const styles =
    variant === "primary"
      ? "bg-slate-900 text-white hover:bg-slate-800 disabled:opacity-60"
      : variant === "danger"
      ? "bg-red-600 text-white hover:bg-red-700 focus:ring-2 focus:ring-red-400"
      : variant === "success"
      ? "bg-emerald-600 text-white hover:bg-emerald-700 focus:ring-2 focus:ring-emerald-400"
      : variant === "warning"
      ? "bg-yellow-600 text-white hover:bg-yellow-700 focus:ring-2 focus:ring-yellow-400"
      : "border border-slate-200 text-slate-900 hover:bg-slate-50 disabled:opacity-60";

  const cls = [base, styles, className].join(" ");

  if (to) {
    return (
      <Link to={to} state={state} className={cls}>
        {children}
      </Link>
    );
  }

  return (
    <button {...props} className={cls}>
      {children}
    </button>
  );
}

export default Button;
