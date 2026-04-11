// src/features/books/components/BookViewMode.jsx
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
  return (
    <div className="mt-4">
      {/* Cover + grouped info */}
      <div className="flex flex-col gap-8 sm:flex-row">
        {/* Cover art */}
        <div className="flex-shrink-0">
          <CoverImage
            path={book.cover_image_path}
            title={book.title}
            className="h-[30rem] w-80"
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
              <div className="grid grid-cols-2 gap-4">
                <DetailField label="Kickstarter tag — ebook">
                  <span className="font-mono">{book.kickstarter_item_tag_ebook || "—"}</span>
                </DetailField>
                <DetailField label="Kickstarter tag — print">
                  <span className="font-mono">{book.kickstarter_item_tag_print || "—"}</span>
                </DetailField>
              </div>
              <DetailField label="Released">
                {book.released ? "Yes" : "No"}
              </DetailField>
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
              <DetailField label="Hand-Sold/Kickstarter">
                {pct(book.hand_sold_author_royalty_rate)}
              </DetailField>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
