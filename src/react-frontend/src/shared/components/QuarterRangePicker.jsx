// src/shared/components/QuarterRangePicker.jsx
import React from "react";
import { QUARTER_OPTIONS } from "../utils/quarterUtils";

const selectClass =
  "rounded-xl border border-slate-200 px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-slate-900";

/**
 * Reusable quarter range picker with start/end year + quarter selectors.
 * Extracted from AuthorRoyaltyReportPage for reuse across report pages.
 */
export function QuarterRangePicker({
  startYear,
  onStartYearChange,
  startQuarter,
  onStartQuarterChange,
  endYear,
  onEndYearChange,
  endQuarter,
  onEndQuarterChange,
}) {
  return (
    <>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Start Quarter
        </label>
        <div className="flex gap-1">
          <input
            type="number"
            className={`${selectClass} year-input`}
            value={startYear}
            onChange={(e) => onStartYearChange(e.target.value)}
            onWheel={(e) => e.target.blur()}
            style={{ width: "80px" }}
          />
          <select
            className={selectClass}
            value={startQuarter}
            onChange={(e) => onStartQuarterChange(Number(e.target.value))}
          >
            {QUARTER_OPTIONS.map((q) => (
              <option key={q} value={q}>Q{q}</option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          End Quarter
        </label>
        <div className="flex gap-1">
          <input
            type="number"
            className={`${selectClass} year-input`}
            value={endYear}
            onChange={(e) => onEndYearChange(e.target.value)}
            onWheel={(e) => e.target.blur()}
            style={{ width: "80px" }}
          />
          <select
            className={selectClass}
            value={endQuarter}
            onChange={(e) => onEndQuarterChange(Number(e.target.value))}
          >
            {QUARTER_OPTIONS.map((q) => (
              <option key={q} value={q}>Q{q}</option>
            ))}
          </select>
        </div>
      </div>
    </>
  );
}

export default QuarterRangePicker;
