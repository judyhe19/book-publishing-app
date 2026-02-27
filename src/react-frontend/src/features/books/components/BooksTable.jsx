// src/features/books/components/BooksTable.jsx
import React from "react";
import { DataTable } from "../../../shared/components";
import { formatMonthYear } from "../../../shared/utils/dateUtils";

function pct(x) {
  const n = Number(x);
  if (Number.isNaN(n)) return "";
  return `${(n * 100).toFixed(1)}%`;
}

const BOOKS_COLUMNS = [
  {
    label: "Title",
    sortKey: "title",
    className: "whitespace-normal",
    render: (b) => <span className="font-medium text-slate-700">{b.title}</span>,
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
    },
  },
  {
    label: "ISBN-13",
    sortKey: "isbn_13",
    render: (b) => <span className="font-mono text-slate-700">{b.isbn_13 || "—"}</span>,
  },
  {
    label: "ISBN-10",
    sortKey: "isbn_10",
    render: (b) => <span className="font-mono text-slate-700">{b.isbn_10 || "—"}</span>,
  },
  {
    label: "Publication",
    sortKey: "publication_date",
    render: (b) => formatMonthYear(b.publication_date),
  },
  {
    label: "Royalty Rate",
    sortKey: "author_royalty_rate",
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
    },
  },
  {
    label: "Total Sales",
    sortKey: "total_sales_to_date",
    render: (b) => <span className="tabular-nums">{b.total_sales_to_date ?? 0}</span>,
  },
];

export default function BooksTable({ books, ordering, onToggleOrdering, onGoBook }) {
  return (
    <DataTable
      data={books}
      columns={BOOKS_COLUMNS}
      loading={false}
      ordering={ordering}
      onSort={onToggleOrdering}
      onRowClick={(b) => onGoBook?.(b)}
      emptyMessage="No books found."
    />
  );
}
