// src/shared/components/PaymentStatusBadge.jsx
import React from "react";

/**
 * Payment status indicator badge.
 * Shows paid/unpaid/partial status with consistent styling.
 * 
 * Variants:
 * - "paid" / "success": Green badge
 * - "unpaid" / "danger": Red badge  
 * - "partial" / "warning": Amber badge
 * - "dot": Minimal dot-only display (for inline use)
 */
export function PaymentStatusBadge({ 
  status, 
  variant = "badge",
  className = "" 
}) {
  const configs = {
    paid: {
      dot: "bg-green-500 rounded-full",
      badge: "bg-green-100 text-green-700",
      label: "Paid",
    },
    success: {
      dot: "bg-green-500 rounded-full",
      badge: "bg-green-100 text-green-700",
      label: "Fully Paid",
    },
    unpaid: {
      dot: "bg-red-500",
      badge: "bg-red-100 text-red-700",
      label: "Unpaid",
    },
    danger: {
      dot: "bg-red-500",
      badge: "bg-red-100 text-red-700",
      label: "Unpaid",
    },
    partial: {
      dot: "bg-amber-500 rounded-full",
      badge: "bg-amber-100 text-amber-700",
      label: "Partially Paid",
    },
    warning: {
      dot: "bg-amber-500 rounded-full",
      badge: "bg-amber-100 text-amber-700",
      label: "Partially Paid",
    },
  };

  const config = configs[status] || configs.unpaid;

  if (variant === "dot") {
    return (
      <span 
        className={`w-2 h-2 inline-block ${config.dot} ${className}`} 
        title={config.label}
      />
    );
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${config.badge} ${className}`}>
      <span className={`w-2 h-2 ${config.dot}`} />
      {config.label}
    </span>
  );
}

export default PaymentStatusBadge;
