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
    label: "Cover",
    sortKey: null,
    render: (b) =>
      b.cover_image_path ? (
        <img
          src={b.cover_image_path}
          alt={`${b.title} cover`}
          className="h-12 w-8 object-cover rounded shadow-sm"
        />
      ) : (
        <span className="text-slate-400">—</span>
      ),
  },
  {
    label: "Title",
    sortKey: "title",
    className: "whitespace-normal",
    render: (b) => (
      <span className="font-medium text-slate-700">{b.title}</span>
    ),
  },
  {
    label: "Author",
    sortKey: "first_author_name",
    className: "whitespace-nowrap",
    render: (b) =>
      b.author_name ? (
        <span className="text-slate-700">{b.author_name}</span>
      ) : (
        <span className="text-slate-400">—</span>
      ),
  },
  {
    label: "Series",
    sortKey: "series_name",
    render: (b) =>
      b.series_name ? (
        <span className="text-slate-700">
          {b.series_name} ({b.series_position})
        </span>
      ) : (
        <span className="text-slate-400">—</span>
      ),
  },
  {
    label: "ISBN-13",
    sortKey: "isbn_13",
    render: (b) => (
      <span className="font-mono text-slate-700">
        {b.isbn_13 || "—"}
      </span>
    ),
  },
  {
    label: "Publication",
    sortKey: "publication_date",
    render: (b) => formatMonthYear(b.publication_date),
  },
  {
    label: "Total Sales",
    sortKey: "total_sales_to_date",
    render: (b) => (
      <span className="tabular-nums">
        {b.total_sales_to_date ?? 0}
      </span>
    ),
  },
];

export default function BooksTable({
  books,
  ordering,
  onToggleOrdering,
  onGoBook,
}) {
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