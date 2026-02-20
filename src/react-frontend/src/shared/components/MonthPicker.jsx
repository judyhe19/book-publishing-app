import React, { useState, useEffect } from "react";
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
  // A supported browser sanitizes the invalid date to an empty string.
  // An unsupported browser (falls back to "text") keeps "invalid-date".
  return input.type === "month" && input.value !== "invalid-date";
})();

function parseMonthString(val) {
  if (!val) return null;
  const [y, m] = val.split("-").map(Number);
  if (!y || !m) return null;
  return new Date(y, m - 1, 1, 12, 0, 0);
}

function formatMonthDate(date) {
  if (!date) return "";
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  return `${y}-${m}`;
}

export default function MonthPicker({
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

  return (
    <div className={className}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      {isMonthInputSupported ? (
        <input
          type="month"
          name={name}
          className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent bg-white"
          value={value || ""}
          onChange={(e) => onChange(e.target.value)}
          min={min || undefined}
          required={required}
        />
      ) : (
        <DatePicker
          selected={selectedDate}
          onChange={(date) => onChange(formatMonthDate(date))}
          dateFormat={["MM/yyyy", "MM-yyyy", "MMM yyyy", "MMM, yyyy", "MMMM yyyy", "MM/yy", "MM-yy", "M/yyyy"]}
          showMonthYearPicker
          minDate={minDate}
          required={required}
          name={name}
          className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent bg-white"
          placeholderText="e.g. 02/2026 or Feb 2026"
        />
      )}
    </div>
  );
}
