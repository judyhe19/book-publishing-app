// src/shared/components/ErrorAlert.jsx
import React from "react";

/**
 * Consistent error alert styling.
 * Replaces the various inline error box styles across the app.
 * 
 * Variants:
 * - "default" (red): General errors
 * - "warning" (amber): Warnings that aren't blocking
 * - "left-border": Alternative style with left border accent
 */
export function ErrorAlert({ 
  children, 
  variant = "default",
  className = "" 
}) {
  const baseStyles = "px-3 py-2 text-sm whitespace-pre-wrap";
  
  const variantStyles = {
    default: "rounded-xl border border-red-200 bg-red-50 text-red-700",
    warning: "rounded-xl border border-amber-200 bg-amber-50 text-amber-900",
    leftBorder: "bg-red-50 border-l-4 border-red-400 p-4 rounded-md text-red-700",
  };

  return (
    <div className={`${baseStyles} ${variantStyles[variant]} ${className}`}>
      {children}
    </div>
  );
}

export default ErrorAlert;
