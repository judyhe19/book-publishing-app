// src/features/sales/components/SaleInputRow.jsx
import React, { useCallback } from "react";
import AsyncSelect from "react-select/async";
import {
  Input,
  MonthPicker,
} from "../../../shared/components";
import { Card } from "../../../shared/components/Card";
import { useBookSearch } from "../../../shared/hooks/useBookSearch";
import { computeAuthorRoyalty, computeHandsoldRevenue } from "../../../shared/utils/salesUtils";
import { formatMoney } from "../../../shared/utils/formatUtils";

const selectStyles = {
  menuPortal: (base) => ({ ...base, zIndex: 9999 }),
  control: (base) => ({
    ...base,
    borderRadius: "0.75rem",
    borderColor: "#e2e8f0",
    boxShadow: "none",
    "&:hover": { borderColor: "#e2e8f0" },
  }),
};

export default function SaleInputRow({ index, row, onChange, onRemove, isFirst }) {
  const { loadOptions } = useBookSearch({ date: row.date });

  const isDistributor = row.sale_source === "distributor";

  const handleField = (field, value) => onChange(index, field, value);

  const handleBookChange = useCallback(
    (option) => {
      onChange(index, "book", option);
      // Recompute derived fields for the new book
      if (row.sale_source === "handsold") {
        const revenue = computeHandsoldRevenue(option, row.quantity);
        onChange(index, "publisher_revenue", revenue);
      }
    },
    [index, onChange, row.sale_source]
  );

  const handleSaleSourceChange = (source) => {
    handleField("sale_source", source);
    if (source === "handsold") {
      // TODO: auto-compute publisher revenue once Book has cover_price / print_cost
      const revenue = computeHandsoldRevenue(row.book, row.quantity);
      handleField("publisher_revenue", revenue);
    } else {
      // Clear publisher revenue so user can enter it manually
      handleField("publisher_revenue", "");
    }
  };

  const handleDateChange = (newDate) => {
    handleField("date", newDate);
    // Clear book if its publication date is after the new sale date
    if (row.book?.publication_date && newDate) {
      const [sy, sm] = newDate.split("-").map(Number);
      const [py, pm] = row.book.publication_date.split("-").map(Number);
      if (py * 100 + pm > sy * 100 + sm) {
        onChange(index, "book", null);
      }
    }
  };

  // Compute auto-royalty for display
  const autoRoyalty = computeAuthorRoyalty(row.sale_source, row.publisher_revenue, row.book);

  return (
    <Card>
      <div className="p-4 bg-white rounded-2xl relative space-y-4">
        {/* Row 1: Date + Book */}
        <div className="flex flex-wrap gap-4 items-start">
          <div className="w-48">
            <MonthPicker
              label="Month/Year"
              value={row.date}
              onChange={handleDateChange}
              min={row.book?.publication_date}
            />
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Book (Title or ISBN)
            </label>
            <AsyncSelect
              key={row.date || "default"}
              cacheOptions
              loadOptions={loadOptions}
              defaultOptions
              onChange={handleBookChange}
              value={row.book}
              placeholder="Search..."
              menuPortalTarget={document.body}
              styles={selectStyles}
            />
          </div>
        </div>

        {/* Row 2: Sale Source + Quantity + Revenue + Royalty */}
        <div className="flex flex-wrap gap-4 items-end">
          {/* Sale Source */}
          <div className="w-40">
            <label className="block text-sm font-medium text-gray-700 mb-1">Sale Source</label>
            <input
              list="source-options"
              value={row.sale_source}
              onChange={(e) => handleSaleSourceChange(e.target.value.toLowerCase())}
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent bg-white capitalize"
              placeholder="Type or select..."
            />
            <datalist id="source-options">
              <option value="Distributor" />
              <option value="Handsold" />
            </datalist>
          </div>

          {/* Quantity */}
          <div className="w-28">
            <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
            <Input
              type="number"
              min="1"
              step="1"
              value={row.quantity}
              onChange={(e) => handleField("quantity", e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "." || e.key === "e" || e.key === "E") e.preventDefault();
              }}
            />
          </div>

          {/* Publisher Revenue */}
          <div className="w-36">
            <label className="block text-sm font-medium text-gray-700 mb-1">Revenue</label>
            {isDistributor ? (
              <div className="relative">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                  <span className="text-gray-500 text-sm">$</span>
                </div>
                <Input
                  type="number"
                  step="0.01"
                  className="pl-7"
                  placeholder="0.00"
                  value={row.publisher_revenue}
                  onChange={(e) => handleField("publisher_revenue", e.target.value)}
                />
              </div>
            ) : (
              <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200 h-[38px] flex items-center">
                {/* TODO: Will show computed revenue once Book has cover_price / print_cost */}
                {row.publisher_revenue ? formatMoney(row.publisher_revenue) : "—"}
              </div>
            )}
          </div>

          {/* Author Royalty (auto-computed, read-only) */}
          <div className="w-36">
            <label className="block text-sm font-medium text-gray-700 mb-1">Author Royalty</label>
            <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200 h-[38px] flex items-center">
              {autoRoyalty ? `$${autoRoyalty}` : "—"}
            </div>
          </div>
        </div>

        {/* Row 3: Comment */}
        <div className="flex flex-wrap gap-4 items-start">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">Comment</label>
            <textarea
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent bg-white resize-none"
              rows={1}
              placeholder="Optional comment..."
              value={row.comment || ""}
              onChange={(e) => handleField("comment", e.target.value)}
            />
          </div>
        </div>

        {/* Remove button */}
        {!isFirst && (
          <button
            onClick={() => onRemove(index)}
            className="text-red-500 hover:text-red-700 p-2 absolute right-0 top-0 mt-2 mr-2"
            title="Remove row"
          >
            ✕
          </button>
        )}
      </div>
    </Card>
  );
}
