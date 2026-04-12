// src/features/sales/components/SaleInputRow.jsx
import React, { useCallback, useState, useEffect } from "react";
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

export default function SaleInputRow({ index, row, onChange, onBlur, onRemove, isFirst, fixedBook }) {
  const fireBlur = () => onBlur?.(index);
  const { loadOptions } = useBookSearch({ date: row.date });

  // If a fixedBook is provided, use it as the effective book for calculations
  const effectiveBook = fixedBook || row.book;

  const isDistributor = row.sale_source === "distributor";
  const isHandsold = row.sale_source === "handsold";
  const isKickstarter = row.sale_source === "kickstarter";
  const isComputedRevenue = isHandsold || isKickstarter;
  const isKU = row.format === "kindle unlimited";

  const handleField = (field, value) => onChange(index, field, value);

  const handleBookChange = useCallback(
    (option) => {
      onChange(index, "book", option);
      // Recompute derived fields for the new book
      if (row.sale_source === "handsold" || row.sale_source === "kickstarter") {
        const revenue = computeHandsoldRevenue(option, row.quantity);
        onChange(index, "publisher_revenue", revenue);
      }
    },
    [index, onChange, row.sale_source, row.quantity]
  );

  const handleSaleSourceChange = (source) => {
    handleField("sale_source", source);
    if (source === "handsold" || source === "kickstarter") {
      const revenue = computeHandsoldRevenue(effectiveBook, row.quantity);
      handleField("publisher_revenue", revenue);
      handleField("currency", "USD");
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
  const autoRoyalty = computeAuthorRoyalty(row.sale_source, row.publisher_revenue, effectiveBook);

  const [currencyError, setCurrencyError] = useState(null);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!isDistributor || !row.currency || row.currency === "USD") {
      setCurrencyError(null);
      return;
    }

    const amount = Number(row.publisher_revenue_original);
    if (Number.isNaN(amount) || amount <= 0) {
      if (row.publisher_revenue !== "") {
        onChange(index, "publisher_revenue", "");
      }
      setCurrencyError(null);
      return;
    }

    const timeoutId = setTimeout(() => {
      import("../api/salesApi").then(({ convertCurrency }) => {
        convertCurrency(amount, row.currency)
          .then((res) => {
            setCurrencyError(null);
            if (res.usd_amount) {
              const formattedUsd = Number(res.usd_amount).toFixed(2);
              if (formattedUsd !== String(row.publisher_revenue)) {
                onChange(index, "publisher_revenue", formattedUsd);
              }
            }
          })
          .catch((err) => {
            const errorMsg = err.error || err.message || (typeof err === "string" ? err : "Invalid currency.");
            setCurrencyError(errorMsg);
            onChange(index, "publisher_revenue", "");
          });
      });
    }, 600);

    return () => clearTimeout(timeoutId);
  }, [row.publisher_revenue_original, row.currency, isDistributor]);

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
              Book (Title, ISBN or ASIN)
            </label>
            {fixedBook ? (
              <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200 h-[38px] flex items-center">
                {fixedBook.label}
              </div>
            ) : (
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
            )}
          </div>
        </div>

        {/* Row 2: Sale Source + Format + Distributor + Quantity/KENP + Currency + Revenue + Royalty */}
        <div className="flex flex-wrap gap-4 items-end">
          {/* Sale Source */}
          <div className="w-40">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Sale Source
            </label>

            <select
              value={row.sale_source || ""}
              onChange={(e) => handleSaleSourceChange(e.target.value)}
              onBlur={fireBlur}
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent bg-white"
            >
              <option value="" disabled>
                Select...
              </option>
              <option value="distributor">Distributor</option>
              <option value="handsold">Handsold</option>
              <option value="kickstarter">Kickstarter</option>
            </select>
          </div>

          {/* Format */}
          <div className="w-44">
            <label className="block text-sm font-medium text-gray-700 mb-1">Format</label>
            <select
              value={row.format || ""}
              onChange={(e) => handleField("format", e.target.value)}
              onBlur={fireBlur}
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent bg-white"
            >
              <option value="" disabled>Select...</option>
              <option value="print">Print</option>
              <option value="ebook">eBook</option>
              <option value="kindle unlimited">Kindle Unlimited</option>
            </select>
          </div>

          {/* Distributor — only for distributor sales */}
          {isDistributor && (
            <div className="w-36">
              <label className="block text-sm font-medium text-gray-700 mb-1">Distributor</label>
              <select
                value={row.distributor || ""}
                onChange={(e) => handleField("distributor", e.target.value)}
                onBlur={fireBlur}
                className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent bg-white"
              >
                <option value="" disabled>Select...</option>
                <option value="Ingram Spark">Ingram Spark</option>
                <option value="Amazon">Amazon</option>
                <option value="Other">Other</option>
              </select>
            </div>
          )}

          {/* Quantity (print/ebook) or KENP (Kindle Unlimited) */}
          {isKU ? (
            <div className="w-28 relative">
              <label className="block text-sm font-medium text-gray-700 mb-1">KENP</label>
              <Input
                type="number"
                min="1"
                step="1"
                value={row.kenp || ""}
                onChange={(e) => handleField("kenp", e.target.value)}
                onBlur={fireBlur}
                onKeyDown={(e) => {
                  if (e.key === "." || e.key === "e" || e.key === "E") e.preventDefault();
                }}
              />
            </div>
          ) : (
            <div className="w-28 relative">
              <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
              <Input
                type="number"
                min="1"
                step="1"
                value={row.quantity}
                onChange={(e) => {
                  const qty = e.target.value;
                  handleField("quantity", qty);
                  // Recompute revenue when quantity changes for handsold/kickstarter
                  if (isComputedRevenue && effectiveBook) {
                    const revenue = computeHandsoldRevenue(effectiveBook, qty);
                    handleField("publisher_revenue", revenue);
                  }
                }}
                onBlur={fireBlur}
                onKeyDown={(e) => {
                  if (e.key === "." || e.key === "e" || e.key === "E") e.preventDefault();
                }}
              />
              {row.quantity !== "" && Number(row.quantity) < 1 && (
                <p className="absolute text-xs text-red-500 mt-0.5">Must be ≥ 1</p>
              )}
            </div>
          )}

          {/* Currency */}
          <div className="w-20">
            <label className="block text-sm font-medium text-gray-700 mb-1">Currency</label>
            <Input
              type="text"
              placeholder="USD"
              value={row.currency || ""}
              onChange={(e) => {
                setCurrencyError(null);
                handleField("currency", e.target.value.toUpperCase());
              }}
              onBlur={fireBlur}
              className={currencyError ? "border-red-500 bg-red-50 text-red-900" : ""}
            />
          </div>

          {/* Publisher Revenue */}
          <div className="w-40">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {isDistributor && row.currency && row.currency !== 'USD' ? `Revenue (${row.currency})` : 'Revenue (USD)'}
            </label>
            {isDistributor ? (
              <div className="relative">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                  <span className="text-gray-500 text-sm">
                    {!row.currency || row.currency === 'USD' ? '$' : row.currency}
                  </span>
                </div>
                <Input
                  type="number"
                  step="0.01"
                  className={(!row.currency || row.currency === 'USD') ? "pl-7" : "pl-12"}
                  placeholder="0.00"
                  value={(!row.currency || row.currency === 'USD') ? row.publisher_revenue : (row.publisher_revenue_original || '')}
                  onChange={(e) => {
                    if (!row.currency || row.currency === 'USD') {
                      handleField("publisher_revenue", e.target.value);
                    } else {
                      handleField("publisher_revenue_original", e.target.value);
                    }
                  }}
                  onBlur={fireBlur}
                />
              </div>
            ) : (
              <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200 h-[38px] flex items-center">
                {row.publisher_revenue ? formatMoney(row.publisher_revenue) : "—"}
              </div>
            )}
          </div>

          {/* Original currency revenue — read-only when non-USD */}
          {isDistributor && row.currency && row.currency !== "USD" && (
            <div className="w-36">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Revenue (USD)
              </label>
              <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200 h-[38px] flex items-center">
                {row.publisher_revenue ? formatMoney(row.publisher_revenue) : "—"}
              </div>
            </div>
          )}

          {/* Author Royalty (auto-computed, read-only) */}
          <div className="w-36">
            <label className="block text-sm font-medium text-gray-700 mb-1">Author Royalty</label>
            <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200 h-[38px] flex items-center">
              {autoRoyalty ? `$${autoRoyalty}` : "—"}
            </div>
          </div>
          {/* Author Paid */}
          <div className="w-24">
            <label className="block text-sm font-medium text-gray-700 mb-1">Author(s) Paid</label>
            <div className="h-[38px] flex items-center px-1">
              <input
                type="checkbox"
                checked={!!row.author_paid}
                onChange={(e) => handleField("author_paid", e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-slate-900 focus:ring-slate-900 cursor-pointer"
              />
            </div>
          </div>
        </div>

        {currencyError && (
          <div className="text-red-500 text-sm mt-1">{currencyError}</div>
        )}

        {/* Row 3: Comment */}
        <div className="flex flex-wrap gap-4 items-start">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">Comment</label>
            <textarea
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent bg-white resize-none"
              rows={1}
              maxLength={256}
              placeholder="Optional comment..."
              value={row.comment || ""}
              onChange={(e) => handleField("comment", e.target.value)}
              onBlur={fireBlur}
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
