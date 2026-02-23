// src/shared/components/StatCard.jsx
import React from "react";

/**
 * Stat card for displaying metrics.
 * Used in BookDetailPage for revenue/royalty totals.
 * 
 * Variants:
 * - "default": Neutral slate styling
 * - "success": Green for positive indicators (e.g., paid)
 * - "danger": Red for negative indicators (e.g., unpaid)
 */
export function StatCard({ 
  label, 
  value, 
  loading = false,
  variant = "default",
  className = "" 
}) {
  const variantStyles = {
    default: "border-slate-200 bg-slate-50",
    success: "border-green-200 bg-green-50",
    danger: "border-red-200 bg-red-50",
  };

  const labelStyles = {
    default: "text-slate-500",
    success: "text-green-600",
    danger: "text-red-600",
  };

  const valueStyles = {
    default: "text-slate-900",
    success: "text-green-700",
    danger: "text-red-700",
  };

  return (
    <div className={`rounded-lg border p-4 ${variantStyles[variant]} ${className}`}>
      <div className={`text-xs font-semibold uppercase ${labelStyles[variant]}`}>
        {label}
      </div>
      <div className={`mt-1 text-lg font-semibold ${valueStyles[variant]}`}>
        {loading ? "Loading…" : value}
      </div>
    </div>
  );
}

export default StatCard;
