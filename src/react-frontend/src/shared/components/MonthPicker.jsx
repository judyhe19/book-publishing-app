// src/shared/components/MonthPicker.jsx
import React from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";

/**
 * Shared month picker — single source of truth for all YYYY-MM date inputs.
 * Uses native <input type="month"> where supported for best keyboard/arrow UX,
 * with a fallback to react-datepicker for browsers that lack support (like Safari).
 */

const isMonthInputSupported = (() => {
  if (typeof document === "undefined") return true; // SSR guard
  const input = document.createElement("input");
  input.type = "month";
  input.value = "invalid-date";
  return input.type === "month" && input.value !== "invalid-date";
})();

function parseMonthString(val) {
  if (!val) return null;
  const parts = val.split("-");
  if (parts.length !== 2) return null;
  const y = parseInt(parts[0], 10);
  const m = parseInt(parts[1], 10);
  if (isNaN(y) || isNaN(m)) return null;
  const d = new Date(y, m - 1, 1, 12, 0, 0);
  d.setFullYear(y);
  return d;
}

function formatMonthDate(date) {
  if (!date) return "";
  const y = String(date.getFullYear()).padStart(4, "0");
  const m = String(date.getMonth() + 1).padStart(2, "0");
  return `${y}-${m}`;
}

export function MonthPicker({
  label,
  value,
  onChange,
  name,
  min,
  required = false,
  className = "",
}) {
  const selectedDate = parseMonthString(value);
  const minDate = parseMonthString(min);
  const maxDate = new Date(9999, 11, 1);

  return (
    <div className={className}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      )}
      {isMonthInputSupported ? (
        <input
          type="month"
          name={name}
          className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent bg-white"
          value={value || ""}
          onChange={(e) => onChange(e.target.value)}
          min={min || undefined}
          max="9999-12"
          required={required}
        />
      ) : (
        <DatePicker
          selected={selectedDate}
          onChange={(date) => onChange(formatMonthDate(date))}
          dateFormat={[
            "MM/yyyy",
            "MM-yyyy",
            "MMM yyyy",
            "MMM, yyyy",
            "MMMM yyyy",
            "MM/yy",
            "MM-yy",
            "M/yyyy",
          ]}
          showMonthYearPicker
          minDate={minDate}
          maxDate={maxDate}
          required={required}
          name={name}
          className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent bg-white"
          placeholderText="e.g. 02/2026 or Feb 2026"
        />
      )}
    </div>
  );
}

export default MonthPicker;
