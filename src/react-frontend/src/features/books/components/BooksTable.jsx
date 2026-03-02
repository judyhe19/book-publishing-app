// src/features/books/components/BooksTable.jsx
import React, { useMemo } from "react";
import { DataTable } from "../../../shared/components";
import { formatMonthYear } from "../../../shared/utils/dateUtils";

function money(x) {
  const n = Number(x);
  if (Number.isNaN(n)) return "—";
  return n.toLocaleString(undefined, { style: "currency", currency: "USD" });
}

function getNum(x) {
  const n = Number(x);
  return Number.isNaN(n) ? 0 : n;
}

export function sortBooksDefault(books) {
  const arr = [...(books || [])];
  arr.sort((a, b) => {
    const aa = (a.author_name || "").toLowerCase();
    const ab = (b.author_name || "").toLowerCase();
    if (aa < ab) return -1;
    if (aa > ab) return 1;

    const sa = (a.series_name || "").toLowerCase();
    const sb = (b.series_name || "").toLowerCase();
    const aHasSeries = sa.trim().length > 0;
    const bHasSeries = sb.trim().length > 0;

    if (aHasSeries && !bHasSeries) return -1;
    if (!aHasSeries && bHasSeries) return 1;

    if (sa < sb) return -1;
    if (sa > sb) return 1;

    const pa = a.series_position ?? Number.POSITIVE_INFINITY;
    const pb = b.series_position ?? Number.POSITIVE_INFINITY;
    if (pa < pb) return -1;
    if (pa > pb) return 1;

    const ta = (a.title || "").toLowerCase();
    const tb = (b.title || "").toLowerCase();
    if (ta < tb) return -1;
    if (ta > tb) return 1;
    return 0;
  });
  return arr;
}

function buildBooksColumns({ showAuthor, extraColumns }) {
  const cols = [
    {
      label: "",
      className: "w-16 pr-0",
      render: (b) => {
        if (!b.cover_image_path) return null;
        const src = `/api/books/cover-thumbnail/?path=${encodeURIComponent(b.cover_image_path)}`;
        return (
          <img
            src={src}
            alt={`Cover of ${b.title}`}
            className="h-16 w-auto object-contain rounded"
          />
        );
      },
    },
    {
      label: "Title",
      sortKey: "title",
      className: "w-[24%] whitespace-normal",
      render: (b) => <span className="font-medium text-slate-700">{b.title}</span>,
    },
  ];

  if (showAuthor) {
    cols.push({
      label: "Author",
      sortKey: "author_name",
      className: "w-[16%] whitespace-nowrap",
      render: (b) => (
        <span className="text-slate-700">
          {b.author_name || <span className="text-slate-400">—</span>}
        </span>
      ),
    });
  }

  cols.push(
    {
      label: "Series",
      sortKey: "series_name",
      className: "w-[20%] whitespace-nowrap",
      render: (b) =>
        b.series_display ? (
          <span className="text-slate-700">{b.series_display}</span>
        ) : (
          <span className="text-slate-400">—</span>
        ),
    },
    {
      label: "ISBN-13",
      sortKey: "isbn_13",
      className: "w-[14%] whitespace-nowrap",
      render: (b) => <span className="font-mono text-slate-700">{b.isbn_13 || "—"}</span>,
    },
    {
      label: "Publication",
      sortKey: "publication_date",
      className: "w-[12%] whitespace-nowrap",
      render: (b) => formatMonthYear(b.publication_date),
    },
    {
      label: "Total Sales",
      sortKey: "total_sales_to_date",
      className: "w-[10%] whitespace-nowrap",
      render: (b) => <span className="tabular-nums">{b.total_sales_to_date ?? 0}</span>,
    }
  );

  if (extraColumns && extraColumns.length) {
    cols.push(...extraColumns);
  }

  return cols;
}

export function buildAuthorRoyaltyColumns() {
  return [
    {
      label: "Total Author Royalty",
      sortKey: "total_author_royalty",
      className: "whitespace-nowrap",
      render: (b) => (
        <span className="tabular-nums">{money(getNum(b.total_author_royalty ?? 0))}</span>
      ),
    },
    {
      label: "Paid Author Royalty",
      sortKey: "paid_author_royalty",
      className: "whitespace-nowrap",
      render: (b) => (
        <span className="tabular-nums">{money(getNum(b.paid_author_royalty ?? 0))}</span>
      ),
    },
    {
      label: "Unpaid Author Royalty",
      sortKey: "unpaid_author_royalty",
      className: "whitespace-nowrap",
      render: (b) => (
        <span className="tabular-nums">{money(getNum(b.unpaid_author_royalty ?? 0))}</span>
      ),
    },
  ];
}

export default function BooksTable({
  books,
  ordering,
  onToggleOrdering,
  onGoBook,
  showAuthor = true,
  extraColumns = [],
  sortable = true,
}) {
  const columns = useMemo(
    () => buildBooksColumns({ showAuthor, extraColumns }),
    [showAuthor, extraColumns]
  );

  return (
    <DataTable
      data={books}
      columns={columns}
      loading={false}
      ordering={ordering}
      onSort={sortable ? onToggleOrdering : undefined}
      onRowClick={(b) => onGoBook?.(b)}
      emptyMessage="No books found."
      fixedLayout
    />
  );
}
