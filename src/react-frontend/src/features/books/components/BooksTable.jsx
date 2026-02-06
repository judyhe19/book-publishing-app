// src/features/books/components/BooksTable.jsx
import React from "react";
import { Card, CardContent } from "../../../shared/components/Card";
import { Button } from "../../../shared/components/Button";

/**
 * Helpers
 */
function formatMonthYear(dateStr) {
  if (!dateStr) return "";

  // Expect "YYYY-MM-DD"
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(dateStr);
  if (!m) return dateStr;

  const year = Number(m[1]);
  const monthIndex = Number(m[2]) - 1; // 0-based
  if (!Number.isFinite(year) || !Number.isFinite(monthIndex)) return dateStr;

  // Create a UTC date at noon to avoid timezone edge cases entirely
  const d = new Date(Date.UTC(year, monthIndex, 1, 12, 0, 0));
  return d.toLocaleString(undefined, { month: "long", year: "numeric" });
}


function pct(x) {
  const n = Number(x);
  if (Number.isNaN(n)) return "";
  return `${(n * 100).toFixed(1)}%`;
}

function SortIcon({ active, desc }) {
  if (!active) return <span className="text-slate-300">↕</span>;
  return <span className="text-slate-700">{desc ? "↓" : "↑"}</span>;
}

/**
 * BooksTable
 *
 * Note: author + royalty are displayed as stacked lists, like your screenshot.
 * Sorting: we only wire sort clicks for fields your backend supports.
 */
export default function BooksTable({
  books,
  ordering,
  onToggleOrdering,
  onGoBook, // placeholder navigation
}) {
  const isDesc = ordering?.startsWith("-");
  const sortField = isDesc ? ordering.slice(1) : ordering;

  const thBase =
    "px-4 py-3 text-left text-xs font-semibold tracking-wide text-slate-600 uppercase";
  const tdBase = "px-4 py-4 align-top text-sm text-slate-700";
  const clickableTh = `${thBase} cursor-pointer select-none hover:text-slate-900`;

  const canSort = (field) => {
    // must match backend allowed_order_fields
    return new Set([
      "title",
      "isbn_13",
      "isbn_10",
      "publication_date",
      "total_sales_to_date",
      "id",
    ]).has(field);
  };

  const headerCell = (label, field) => {
    const sortable = canSort(field);
    const active = sortField === field;
    return (
      <th
        className={sortable ? clickableTh : thBase}
        onClick={sortable ? () => onToggleOrdering(field) : undefined}
      >
        <div className="inline-flex items-center gap-2">
          <span>{label}</span>
          {sortable ? <SortIcon active={active} desc={active && isDesc} /> : null}
        </div>
      </th>
    );
  };

  return (
    <Card>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="min-w-full border-separate border-spacing-0">
            <thead>
              <tr className="bg-slate-50">
                {headerCell("Title", "title")}
                <th className={thBase}>Author(s)</th>
                {headerCell("ISBN-13", "isbn_13")}
                {headerCell("ISBN-10", "isbn_10")}
                {headerCell("Publication", "publication_date")}
                <th className={thBase}>Royalty Rate</th>
                {headerCell("Total Sales", "total_sales_to_date")}
                <th className={thBase}>Actions</th>
              </tr>
            </thead>

            <tbody>
              {(!books || books.length === 0) && (
                <tr>
                  <td className={`${tdBase} py-8`} colSpan={8}>
                    <div className="text-slate-500">No books found.</div>
                  </td>
                </tr>
              )}

              {(books || []).map((b) => {
                const authors = b.authors || [];
                return (
                  <tr key={b.id} className="border-b border-slate-100">
                    <td className={tdBase}>
                      <button
                        className="text-blue-600 hover:underline font-medium"
                        onClick={() => onGoBook?.(b)}
                        type="button"
                      >
                        {b.title}
                      </button>
                    </td>

                    <td className={tdBase}>
                      <div className="space-y-1">
                        {authors.length === 0 ? (
                          <div className="text-slate-400">—</div>
                        ) : (
                          authors.map((a) => (
                            <div key={a.author_id} className="text-slate-700">
                              {a.name}
                            </div>
                          ))
                        )}
                      </div>
                    </td>

                    <td className={tdBase}>
                      <span className="font-mono text-slate-700">{b.isbn_13 || "—"}</span>
                    </td>

                    <td className={tdBase}>
                      <span className="font-mono text-slate-700">{b.isbn_10 || "—"}</span>
                    </td>

                    <td className={tdBase}>{formatMonthYear(b.publication_date)}</td>

                    <td className={tdBase}>
                      <div className="space-y-1">
                        {authors.length === 0 ? (
                          <div className="text-slate-400">—</div>
                        ) : (
                          authors.map((a) => (
                            <div key={a.author_id} className="text-slate-700">
                              {pct(a.royalty_rate)}
                            </div>
                          ))
                        )}
                      </div>
                    </td>

                    <td className={tdBase}>
                      <span className="tabular-nums">{b.total_sales_to_date ?? 0}</span>
                    </td>

                    <td className={tdBase}>
                      <Button variant="secondary" onClick={() => onGoBook?.(b)}>
                        View
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
