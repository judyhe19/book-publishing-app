// src/features/books/components/BookSalesSection.jsx
import React, { useState, useEffect } from "react";
import {
  Card,
  CardHeader,
  CardContent,
  Button,
  ErrorAlert,
  StatCard,
  Pagination,
  ShowAllToggle,
  SaleEntryRow,
} from "../../../shared/components";
import BookSalesTable from "./BookSalesTable";
import { useBookSales } from "../hooks/useBookSales";
import * as booksApi from "../api/booksApi";
import { createManySales } from "../../sales/api/salesApi";
import { EMPTY_ROW, transformRowToSaleData, isRowComplete } from "../../../shared/utils/salesUtils";
import { errorMessage } from "../../../shared/utils/errors";

function formatMoney(x) {
  return `$${Number(x || 0).toFixed(2)}`;
}

/**
 * Self-contained sales section for BookDetailPage.
 * Handles sales table, stats, pagination, and inline sale entry.
 */
export default function BookSalesSection({ bookId, book, onSaleCreated }) {
  // Sales list
  const {
    sales: bookSales,
    loading: salesLoading,
    ordering: salesOrdering,
    handleSort: handleSalesSort,
    refresh: refreshSales,
    page: salesPage,
    totalPages: salesTotalPages,
    setPage: setSalesPage,
    count: salesCount,
    showAll: salesShowAll,
    toggleShowAll: toggleSalesShowAll,
  } = useBookSales(bookId);

  // Totals
  const [totalsLoading, setTotalsLoading] = useState(true);
  const [totalsErr, setTotalsErr] = useState(null);
  const [totals, setTotals] = useState({
    publisher_revenue: "0",
    total_royalties: "0",
    paid_royalties: "0",
    unpaid_royalties: "0",
  });

  // Inline sale entry
  const [showSaleEntry, setShowSaleEntry] = useState(false);
  const [saleRow, setSaleRow] = useState({ ...EMPTY_ROW });
  const [saleSubmitting, setSaleSubmitting] = useState(false);
  const [saleError, setSaleError] = useState(null);

  const fixedBook = book
    ? {
        value: book.id,
        label: book.title,
        publication_date: book.publication_date,
      }
    : null;

  // Load totals
  useEffect(() => {
    refreshTotals();
  }, [bookId]);

  async function refreshTotals() {
    if (!bookId) return;
    setTotalsLoading(true);
    setTotalsErr(null);
    try {
      const t = await booksApi.getBookSalesTotals(bookId);
      setTotals(t);
    } catch (e) {
      setTotalsErr(errorMessage(e));
    } finally {
      setTotalsLoading(false);
    }
  }

  // Sale entry handlers
  const handleSaleRowChange = (index, field, value) => {
    setSaleRow((prev) => {
      if (typeof field === "object" && field !== null) return { ...prev, ...field };
      return { ...prev, [field]: value };
    });
  };

  const handleSubmitSale = async () => {
    setSaleError(null);
    if (!isRowComplete(saleRow)) {
      setSaleError("Please fill in all fields.");
      return;
    }
    setSaleSubmitting(true);
    try {
      const saleData = transformRowToSaleData(saleRow);
      await createManySales([saleData]);
      setSaleRow({ ...EMPTY_ROW });
      setShowSaleEntry(false);
      refreshSales();
      refreshTotals();
      onSaleCreated?.();
    } catch (e) {
      setSaleError(errorMessage(e));
    } finally {
      setSaleSubmitting(false);
    }
  };

  const handleCancelSale = () => {
    setSaleRow({ ...EMPTY_ROW });
    setSaleError(null);
    setShowSaleEntry(false);
  };

  return (
    <Card>
      <CardHeader title="Sales Records" subtitle="All sales records for this book." />
      <CardContent>
        {/* Add Sale button */}
        <div className="mb-4 flex justify-end">
          {!showSaleEntry && (
            <Button onClick={() => setShowSaleEntry(true)}>Add Sale</Button>
          )}
        </div>

        {/* Inline sale entry form */}
        {showSaleEntry && (
          <div className="mb-6">
            {saleError && <ErrorAlert className="mb-4">{saleError}</ErrorAlert>}

            <SaleEntryRow
              index={0}
              data={saleRow}
              onChange={handleSaleRowChange}
              onRemove={() => {}}
              isFirst={true}
              fixedBook={fixedBook}
            />

            <div className="mt-4 flex justify-end gap-2">
              <Button variant="secondary" onClick={handleCancelSale} disabled={saleSubmitting}>
                Cancel
              </Button>
              <Button onClick={handleSubmitSale} disabled={saleSubmitting}>
                {saleSubmitting ? "Submitting…" : "Submit Sale"}
              </Button>
            </div>
          </div>
        )}

        {totalsErr && <ErrorAlert className="mb-4">{totalsErr}</ErrorAlert>}

        {/* Stat cards */}
        <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard
            label="Publisher Revenue"
            value={formatMoney(totals.publisher_revenue)}
            loading={totalsLoading}
          />
          <StatCard
            label="Total Royalties"
            value={formatMoney(totals.total_royalties)}
            loading={totalsLoading}
          />
          <StatCard
            label="Paid Royalties"
            value={formatMoney(totals.paid_royalties)}
            loading={totalsLoading}
            variant="success"
          />
          <StatCard
            label="Unpaid Royalties"
            value={formatMoney(totals.unpaid_royalties)}
            loading={totalsLoading}
            variant="danger"
          />
        </div>

        {/* Show all toggle */}
        <div className="mb-3 flex items-center justify-end">
          <ShowAllToggle showAll={salesShowAll} onToggle={toggleSalesShowAll} />
        </div>

        {/* Sales table */}
        <BookSalesTable
          data={bookSales}
          loading={salesLoading}
          ordering={salesOrdering}
          onSort={handleSalesSort}
        />

        {/* Pagination */}
        {!salesShowAll && (
          <div className="mt-4">
            <Pagination
              page={salesPage}
              totalPages={salesTotalPages}
              onPrev={() => setSalesPage((p) => Math.max(1, p - 1))}
              onNext={() => setSalesPage((p) => Math.min(salesTotalPages, p + 1))}
            />
          </div>
        )}

        {/* Count */}
        <div className="mt-2 text-sm text-slate-600">
          {salesLoading ? (
            "Loading…"
          ) : (
            <>
              <span className="font-semibold text-slate-900">{salesCount}</span>{" "}
              sale{salesCount === 1 ? "" : "s"} for this book
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
