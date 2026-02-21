// src/shared/components/FormField.jsx
import React from "react";

/**
 * Form field wrapper with label.
 * Provides consistent spacing and label styling for form inputs.
 */
export function FormField({ label, htmlFor, children, className = "" }) {
  return (
    <div className={className}>
      {label && (
        <label 
          htmlFor={htmlFor} 
          className="text-sm font-medium text-slate-700"
        >
          {label}
        </label>
      )}
      <div className={label ? "mt-1" : ""}>
        {children}
      </div>
    </div>
  );
}

export default FormField;
