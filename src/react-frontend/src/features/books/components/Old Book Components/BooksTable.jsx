// src/features/books/components/BooksTable.jsx
import React from "react";
import { Button } from "../../../shared/components/Button";
import { formatMonthYear } from "../../../shared/utils/dateUtils";
import { DataTable } from "../../../shared/components/DataTable";

function pct(x) {
  const n = Number(x);
  if (Number.isNaN(n)) return "";
  return `${(n * 100).toFixed(1)}%`;
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
  const columns = [
    {
      label: "Title",
      sortKey: "title",
      className: "whitespace-normal",
      render: (b) => <span className="font-medium text-slate-700">{b.title}</span>
    },
    {
      label: "Author",
      sortKey: "author_name",
      className: "align-top whitespace-nowrap",
      render: (b) => {
        const authors = b.authors || [];
        if (authors.length === 0) return <div className="text-slate-400">—</div>;
        return (
          <div className="space-y-1">
            {authors.map((a) => (
              <div key={a.author_id} className="text-slate-700">
                {a.name}
              </div>
            ))}
          </div>
        );
      }
    },
    {
      label: "ISBN-13",
      sortKey: "isbn_13",
      render: (b) => <span className="font-mono text-slate-700">{b.isbn_13 || "—"}</span>
    },
    {
      label: "ISBN-10",
      sortKey: "isbn_10",
      render: (b) => <span className="font-mono text-slate-700">{b.isbn_10 || "—"}</span>
    },
    {
      label: "Publication",
      sortKey: "publication_date",
      render: (b) => formatMonthYear(b.publication_date)
    },
    {
      label: "Royalty Rate",
      sortKey: "first_author_royalty_rate",
      className: "align-top whitespace-nowrap",
      render: (b) => {
        const authors = b.authors || [];
        if (authors.length === 0) return <div className="text-slate-400">—</div>;
        return (
          <div className="space-y-1">
            {authors.map((a) => (
              <div key={a.author_id} className="text-slate-700">
                {pct(a.royalty_rate)}
              </div>
            ))}
          </div>
        );
      }
    },
    {
      label: "Total Sales",
      sortKey: "total_sales_to_date",
      render: (b) => <span className="tabular-nums">{b.total_sales_to_date ?? 0}</span>
    }
  ];

  return (
    <DataTable
      data={books}
      columns={columns}
      loading={false} // Loading handled at page level, or adjust if you need it here
      ordering={ordering}
      onSort={onToggleOrdering}
      onRowClick={(b) => onGoBook?.(b)}
      emptyMessage="No books found."
    />
  );
}
