import React from "react";

/**
 * Shared month picker — single source of truth for all YYYY-MM date inputs.
 *
 * Props:
 *   label     – optional label text
 *   value     – YYYY-MM string
 *   onChange  – called with the new YYYY-MM string (NOT the event)
 *   name      – optional input name attribute
 *   min       – optional YYYY-MM minimum
 *   required  – optional boolean
 *   className – optional wrapper className override
 */
export default function MonthPicker({
  label,
  value,
  onChange,
  name,
  min,
  required = false,
  className = "",
}) {
  return (
    <div className={className}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      <input
        type="month"
        name={name}
        className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent bg-white"
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        min={min || undefined}
        required={required}
      />
    </div>
  );
}
