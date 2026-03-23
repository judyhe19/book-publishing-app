// src/features/sales/pages/IngramCSVImportPage.jsx
import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, CardContent, ErrorAlert, MonthPicker } from "../../../shared/components";
import { validateIngramCSV, createManySales } from "../api/salesApi";
import { formatMonthYear } from "../../../shared/utils/salesUtils";
import { formatMoney } from "../../../shared/utils/formatUtils";

export default function IngramCSVImportPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  // Step 1 state: upload
  const [file, setFile] = useState(null);
  const [monthYear, setMonthYear] = useState(""); // "YYYY-MM"
  const [validating, setValidating] = useState(false);
  const [errors, setErrors] = useState(null); // string or string[]

  // Step 2 state: preview
  const [previewRows, setPreviewRows] = useState(null);
  const [importing, setImporting] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files?.[0] || null);
    // Reset preview if user picks a new file
    setPreviewRows(null);
    setErrors(null);
  };

  const handleValidate = async () => {
    setErrors(null);
    setPreviewRows(null);

    if (!file) {
      setErrors("Please select a CSV file.");
      return;
    }
    if (!monthYear) {
      setErrors("Please select the month and year of the sales.");
      return;
    }

    const [yearStr, monthStr] = monthYear.split("-");
    const month = parseInt(monthStr, 10);
    const year = parseInt(yearStr, 10);

    setValidating(true);
    try {
      const data = await validateIngramCSV(file, month, year);
      setPreviewRows(data.preview);
    } catch (err) {
      // Show errors from backend (already newline-joined in err.message)
      if (err.data?.errors) {
        setErrors(err.data.errors);
      } else {
        setErrors(err.message || "Validation failed.");
      }
    } finally {
      setValidating(false);
    }
  };

  const handleConfirmImport = async () => {
    if (!previewRows?.length) return;

    setImporting(true);
    setErrors(null);
    try {
      const salesData = previewRows.map((row) => ({
        book: row.book,
        date: row.date,
        quantity: row.quantity,
        sale_source: row.sale_source,
        distributor: row.distributor,
        format: row.format,
        currency: row.currency,
        publisher_revenue_original: row.publisher_revenue_original,
        publisher_revenue: row.publisher_revenue,
        author_royalty: row.author_royalty,
        author_paid: row.author_paid,
        comment: row.comment,
      }));
      await createManySales(salesData);
      navigate("/sales");
    } catch (err) {
      setErrors(err.message || "Import failed.");
    } finally {
      setImporting(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setMonthYear("");
    setPreviewRows(null);
    setErrors(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-semibold text-gray-900 mb-6 font-display">
        Import from Ingram Spark CSV
      </h1>

      {/* Step 1: Upload */}
      <Card className="mb-6">
        <CardContent>
          <div className="flex flex-wrap gap-4 items-end">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                CSV File
              </label>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm
                  file:mr-3 file:rounded-lg file:border-0 file:bg-slate-900 file:text-white
                  file:px-3 file:py-1 file:text-sm file:cursor-pointer
                  focus:outline-none focus:ring-2 focus:ring-slate-900"
              />
            </div>

            <MonthPicker
              label="Sales Month/Year"
              value={monthYear}
              onChange={setMonthYear}
              className="w-48"
            />

            <Button
              onClick={handleValidate}
              disabled={validating || !file || !monthYear}
            >
              {validating ? "Validating..." : "Validate & Preview"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Errors */}
      {errors && (
        <ErrorAlert variant="leftBorder" className="mb-6">
          {Array.isArray(errors) ? (
            <ul className="list-disc list-inside space-y-1">
              {errors.map((e, i) => (
                <li key={i}>{e}</li>
              ))}
            </ul>
          ) : (
            errors
          )}
        </ErrorAlert>
      )}

      {/* Step 2: Preview */}
      {previewRows && previewRows.length > 0 && (
        <>
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Preview — {previewRows.length} sale{previewRows.length > 1 ? "s" : ""} to import
          </h2>

          <div className="space-y-3 mb-6">
            {previewRows.map((row, idx) => (
              <Card key={idx}>
                <div className="p-4 space-y-3">
                  {/* Row 1: Date + Book */}
                  <div className="flex flex-wrap gap-4 items-start">
                    <div className="w-48">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Month/Year
                      </label>
                      <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200 h-[38px] flex items-center">
                        {formatMonthYear(row.date)}
                      </div>
                    </div>
                    <div className="flex-1 min-w-[200px]">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Book
                      </label>
                      <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200 h-[38px] flex items-center truncate">
                        {row.book_label}
                      </div>
                    </div>
                  </div>

                  {/* Row 2: Source, Distributor, Format, Currency, Qty, Revenue, Royalty */}
                  <div className="flex flex-wrap gap-4 items-end">
                    <div className="w-32">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Sale Source
                      </label>
                      <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200 h-[38px] flex items-center capitalize">
                        {row.sale_source}
                      </div>
                    </div>
                    <div className="w-32">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Distributor
                      </label>
                      <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200 h-[38px] flex items-center">
                        {row.distributor}
                      </div>
                    </div>
                    <div className="w-24">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Format
                      </label>
                      <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200 h-[38px] flex items-center capitalize">
                        {row.format}
                      </div>
                    </div>
                    <div className="w-24">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Currency
                      </label>
                      <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200 h-[38px] flex items-center">
                        {row.currency}
                      </div>
                    </div>
                    <div className="w-24">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Quantity
                      </label>
                      <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200 h-[38px] flex items-center">
                        {row.quantity}
                      </div>
                    </div>
                    <div className="w-32">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Revenue
                      </label>
                      <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200 h-[38px] flex items-center">
                        {formatMoney(row.publisher_revenue)}
                      </div>
                    </div>
                    <div className="w-36">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Author Royalty
                      </label>
                      <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200 h-[38px] flex items-center">
                        {formatMoney(row.author_royalty)}
                      </div>
                    </div>
                    <div className="w-24">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Author Paid
                      </label>
                      <div className="h-[38px] flex items-center px-1">
                        <input
                          type="checkbox"
                          checked={row.author_paid}
                          readOnly
                          disabled
                          className="h-4 w-4 rounded border-gray-300 text-slate-900 focus:ring-slate-900 cursor-not-allowed opacity-50"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Row 3: Comment */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Comment
                    </label>
                    <div className="text-sm text-slate-500 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200 break-words whitespace-pre-wrap">
                      {row.comment}
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-4">
            <Button variant="secondary" onClick={handleReset}>
              Cancel
            </Button>
            <Button onClick={handleConfirmImport} disabled={importing}>
              {importing ? "Importing..." : `Confirm Import (${previewRows.length})`}
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
