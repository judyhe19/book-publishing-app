// src/features/books/components/BookViewMode.jsx
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
    <div className="mt-4">
      {/* Title */}
      <h1 className="text-3xl font-bold leading-tight text-slate-900">{book.title}</h1>

      {/* Author */}
      <div className="mt-2">
        {book.author_id ? (
          <button
            type="button"
            className="text-lg text-blue-600 underline hover:text-blue-800"
            onClick={() => nav(`/authors/${book.author_id}`)}
          >
            {book.author_name || `Author #${book.author_id}`}
          </button>
        ) : (
          <span className="text-lg text-slate-400">No author assigned</span>
        )}
      </div>

      {/* Series */}
      {book.series_name && (
        <p className="mt-1 text-sm italic text-slate-500">
          {book.series_display || `${book.series_name}, Book ${book.series_position}`}
        </p>
      )}

      {/* Cover + grouped info */}
      <div className="mt-6 flex flex-col gap-8 sm:flex-row">
        {/* Cover art */}
        <div className="flex-shrink-0">
          <CoverImage
            path={book.cover_image_path}
            title={book.title}
            className="h-80 w-60"
          />
        </div>

        {/* Info sections */}
        <div className="flex-1 divide-y divide-slate-100">
          {/* Publication Info */}
          <div className="pb-5">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
              Publication Info
            </p>
            <div className="space-y-3">
              <DetailField label="Published">
                {formatMonthYear(book.publication_date)}
              </DetailField>
              <div className="grid grid-cols-3 gap-4">
                <DetailField label="ISBN-13">
                  <span className="font-mono">{book.isbn_13 || "—"}</span>
                </DetailField>
                <DetailField label="ISBN-10">
                  <span className="font-mono">{book.isbn_10 || "—"}</span>
                </DetailField>
                <DetailField label="Amazon ASIN (ebook)">
                  <span className="font-mono">{book.amazon_asin_ebook || "—"}</span>
                </DetailField>
              </div>
              {/* {book.amazon_asin_ebook && (
                <DetailField label="Amazon ASIN (ebook)">
                  <span className="font-mono">{book.amazon_asin_ebook}</span>
                </DetailField>
              )} */}
            </div>
          </div>

          {/* Pricing & Sales */}
          <div className="py-5">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
              Pricing & Sales
            </p>
            <div className="grid grid-cols-3 gap-4">
              <DetailField label="Cover Price">
                {book.cover_price != null ? formatMoney(book.cover_price) : "—"}
              </DetailField>
              <DetailField label="Print Cost">
                {book.print_cost != null ? formatMoney(book.print_cost) : "—"}
              </DetailField>
              <DetailField label="Total Sales">
                {book.total_sales_to_date ?? 0}
              </DetailField>
            </div>
          </div>

          {/* Royalty Rates */}
          <div className="pt-5">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
              Royalty Rates
            </p>
            <div className="grid grid-cols-2 gap-4">
              <DetailField label="Distributor">
                {pct(book.distributor_author_royalty_rate)}
              </DetailField>
              <DetailField label="Hand-Sold">
                {pct(book.hand_sold_author_royalty_rate)}
              </DetailField>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
