// src/features/books/components/BookViewMode.jsx
import React from "react";
import { useNavigate } from "react-router-dom";
import { DetailField } from "../../../shared/components";
import { formatMonthYear } from "../../../shared/utils/dateUtils";
import CoverImage from "./CoverImage";

function pct(x) {
  const n = Number(x);
  if (Number.isNaN(n)) return "—";
  return `${(n * 100).toFixed(1)}%`;
}

function formatMoney(x) {
  return `$${Number(x || 0).toFixed(2)}`;
}

/**
 * Read-only view of book details.
 * Used in BookDetailPage when not in edit mode.
 */
export default function BookViewMode({ book }) {
  const nav = useNavigate();

  return (
    <div className="mt-6 flex flex-col gap-6 sm:flex-row">
      {/* Cover art */}
      <CoverImage path={book.cover_image_path} title={book.title} />

      {/* Metadata */}
      <div className="flex-1 space-y-4">
        <DetailField label="Title">{book.title}</DetailField>

        <DetailField label="Author">
          {book.author_id ? (
            <button
              type="button"
              className="text-blue-600 underline hover:text-blue-800"
              onClick={() => nav(`/authors/${book.author_id}`)}
            >
              {book.author_name || `Author #${book.author_id}`}
            </button>
          ) : (
            "—"
          )}
        </DetailField>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <DetailField label="Publication">
            {formatMonthYear(book.publication_date)}
          </DetailField>
          <DetailField label="Total Sales">
            {book.total_sales_to_date ?? 0}
          </DetailField>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <DetailField label="ISBN-13">
            <span className="font-mono">{book.isbn_13 || "—"}</span>
          </DetailField>
          <DetailField label="ISBN-10">
            <span className="font-mono">{book.isbn_10 || "—"}</span>
          </DetailField>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <DetailField label="Cover Price">
            {book.cover_price != null ? formatMoney(book.cover_price) : "—"}
          </DetailField>
          <DetailField label="Print Cost">
            {book.print_cost != null ? formatMoney(book.print_cost) : "—"}
          </DetailField>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <DetailField label="Distributor Royalty Rate">
            {pct(book.distributor_author_royalty_rate)}
          </DetailField>
          <DetailField label="Hand-Sold Royalty Rate">
            {pct(book.hand_sold_author_royalty_rate)}
          </DetailField>
        </div>

        {book.series_name && (
          <DetailField label="Series">
            {book.series_display || `${book.series_name} (${book.series_position})`}
          </DetailField>
        )}

      </div>
    </div>
  );
}
