// src/features/books/components/SeriesFields.jsx
import React from "react";
import { FormField, Input } from "../../../shared/components";

/**
 * Series name and position fields with edit warning.
 * Used in BookDetailPage edit mode.
 */
export default function SeriesFields({
  seriesName,
  setSeriesName,
  seriesPosition,
  setSeriesPosition,
}) {
  return (
    <div className="rounded-md border border-amber-200 bg-amber-50 p-4 space-y-3">
      <p className="text-xs text-amber-700">
        <strong>Series editing note:</strong> If swapping positions with another book, first
        clear one book's series fields, save, then assign the new position. This avoids
        uniqueness conflicts.
      </p>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <FormField label="Series name (optional)">
          <Input
            value={seriesName}
            onChange={(e) => setSeriesName(e.target.value)}
            placeholder="e.g. The Lord of the Rings"
          />
        </FormField>
        <FormField label="Series position (optional)">
          <Input
            type="number"
            min="1"
            value={seriesPosition}
            onChange={(e) => setSeriesPosition(e.target.value)}
            placeholder="e.g. 1"
          />
        </FormField>
      </div>
      <div>
        <button
          type="button"
          className="text-xs text-slate-500 underline hover:text-red-600"
          onClick={() => {
            setSeriesName("");
            setSeriesPosition("");
          }}
        >
          Clear series fields
        </button>
      </div>
    </div>
  );
}
