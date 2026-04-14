// src/features/sales/pages/BackerkitXLSXImportPage.jsx
import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, CardContent, ErrorAlert, ConfirmDialog } from "../../../shared/components";
import { importBackerkitXLSX, createManySales } from "../api/salesApi";
import { formatMonthYear } from "../../../shared/utils/salesUtils";
import { formatMoney } from "../../../shared/utils/formatUtils";

const FORMAT_LABELS = {
  print: "Print",
  ebook: "eBook",
};

/** Split a flat warnings array into skipped-row warnings and unknown-tag warnings. */
function partitionWarnings(warnings) {
  const skippedRows = [];
  const unknownTags = [];
  for (const w of warnings) {
    if (w.startsWith("Rows with unsuccessful pledge status")) {
      skippedRows.push(w);
    } else if (w.startsWith("Unknown Kickstarter item tag")) {
      unknownTags.push(w);
    } else {
      unknownTags.push(w); // fallback: treat as unknown-tag warning
    }
  }
  return { skippedRows, unknownTags };
}

export default function BackerkitXLSXImportPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  // Step 1 state: upload
  const [file, setFile] = useState(null);
  const [validating, setValidating] = useState(false);
  const [errors, setErrors] = useState(null);   // string or string[]
  const [skippedRowWarnings, setSkippedRowWarnings] = useState([]);
  const [unknownTagWarnings, setUnknownTagWarnings] = useState([]);

  // Step 2 state: preview
  const [previewRows, setPreviewRows] = useState(null);
  const [importing, setImporting] = useState(false);
  const [showWarningModal, setShowWarningModal] = useState(false);

  const allWarnings = [...skippedRowWarnings, ...unknownTagWarnings];

  const handleFileChange = (e) => {
    setFile(e.target.files?.[0] || null);
    setPreviewRows(null);
    setErrors(null);
    setSkippedRowWarnings([]);
    setUnknownTagWarnings([]);
  };

  const handleValidate = async () => {
    setErrors(null);
    setSkippedRowWarnings([]);
    setUnknownTagWarnings([]);
    setPreviewRows(null);

    if (!file) {
      setErrors("Please select an XLSX file.");
      return;
    }

    setValidating(true);
    try {
      const data = await importBackerkitXLSX(file);
      const { skippedRows, unknownTags } = partitionWarnings(data.warnings ?? []);
      setSkippedRowWarnings(skippedRows);
      setUnknownTagWarnings(unknownTags);
      setPreviewRows(data.preview);
    } catch (err) {
      if (err.data?.errors) {
        setErrors(err.data.errors);
      } else {
        setErrors(err.message || "Validation failed.");
      }
      if (err.data?.warnings?.length) {
        const { skippedRows, unknownTags } = partitionWarnings(err.data.warnings);
        setSkippedRowWarnings(skippedRows);
        setUnknownTagWarnings(unknownTags);
      }
    } finally {
      setValidating(false);
    }
  };

  const doImport = async () => {
    if (!previewRows?.length) return;

    setImporting(true);
    setShowWarningModal(false);
    setErrors(null);
    try {
      const salesData = previewRows.map((row) => ({
        book: row.book,
        date: row.date,
        quantity: row.quantity,
        kenp: null,
        sale_source: row.sale_source,
        distributor: row.distributor ?? null,
        format: row.format,
        currency: row.currency,
        publisher_revenue: row.publisher_revenue,
        publisher_revenue_original: row.publisher_revenue_original ?? null,
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

  const handleConfirmImport = () => {
    if (!previewRows?.length) return;
    if (allWarnings.length > 0) {
      setShowWarningModal(true);
    } else {
      doImport();
    }
  };

  const handleReset = () => {
    setFile(null);
    setPreviewRows(null);
    setErrors(null);
    setSkippedRowWarnings([]);
    setUnknownTagWarnings([]);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-semibold text-gray-900 mb-6 font-display">
        Import from Backerkit XLSX
      </h1>

      {/* Step 1: Upload */}
      <Card className="mb-6">
        <CardContent>
          <div className="flex flex-wrap gap-4 items-end">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                XLSX File
              </label>
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx"
                onChange={handleFileChange}
                className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm
                  file:mr-3 file:rounded-lg file:border-0 file:bg-slate-900 file:text-white
                  file:px-3 file:py-1 file:text-sm file:cursor-pointer
                  focus:outline-none focus:ring-2 focus:ring-slate-900"
              />
            </div>

            <Button
              onClick={handleValidate}
              disabled={validating || !file}
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

      {/* Skipped rows — informational */}
      {skippedRowWarnings.length > 0 && !errors && (
        <div className="mb-6 rounded-xl border border-amber-300 bg-amber-50 p-4">
          <p className="text-sm font-medium text-amber-800 mb-2">
            The following rows were skipped because their pledge status was unsuccessful:
          </p>
          <ul className="list-disc list-inside space-y-1">
            {skippedRowWarnings.map((w, i) => (
              <li key={i} className="text-sm text-amber-700">{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Unknown item tags — informational */}
      {unknownTagWarnings.length > 0 && !errors && (
        <div className="mb-6 rounded-xl border border-amber-300 bg-amber-50 p-4">
          <p className="text-sm font-medium text-amber-800 mb-2">
            The following Kickstarter item tags were not matched to any book (e.g. swag or
            non-royalty items). You will be asked to confirm before importing.
          </p>
          <ul className="list-disc list-inside space-y-1">
            {unknownTagWarnings.map((w, i) => (
              <li key={i} className="text-sm text-amber-700">{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Step 2: Preview — flat list */}
      {previewRows && previewRows.length > 0 && (
        <>
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Preview — {previewRows.length} sale{previewRows.length !== 1 ? "s" : ""} to import
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

                  {/* Row 2: Format, Quantity, Revenue, Author Royalty */}
                  <div className="flex flex-wrap gap-4 items-end">
                    <div className="w-28">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Format
                      </label>
                      <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200 h-[38px] flex items-center">
                        {FORMAT_LABELS[row.format] ?? row.format}
                      </div>
                    </div>

                    <div className="w-28">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Quantity
                      </label>
                      <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200 h-[38px] flex items-center">
                        {row.quantity}
                      </div>
                    </div>

                    <div className="w-36">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Revenue (USD)
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
            <Button onClick={handleConfirmImport} disabled={importing || !previewRows?.length}>
              {importing ? "Importing..." : `Confirm Import (${previewRows.length})`}
            </Button>
          </div>
        </>
      )}

      {/* Warning confirmation modal */}
      <ConfirmDialog
        open={showWarningModal}
        title="Warnings — proceed with import?"
        confirmText="Yes, import"
        onCancel={() => setShowWarningModal(false)}
        onConfirm={doImport}
        confirming={importing}
      >
        <p className="text-slate-600 mb-3">
          The following warnings were raised. Do you still want to import the
          remaining records?
        </p>
        <ul className="list-disc list-inside space-y-1 text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-xl p-3">
          {allWarnings.map((w, i) => (
            <li key={i}>{w}</li>
          ))}
        </ul>
      </ConfirmDialog>
    </div>
  );
}
