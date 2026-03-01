// src/features/books/components/BooksTable.jsx
import React, { useMemo } from "react";
import { DataTable } from "../../../shared/components";
import { formatMonthYear } from "../../../shared/utils/dateUtils";

function pct(x) {
  const n = Number(x);
  if (Number.isNaN(n)) return "";
  return `${(n * 100).toFixed(1)}%`;
}

function money(x) {
  const n = Number(x);
  if (Number.isNaN(n)) return "—";
  return n.toLocaleString(undefined, { style: "currency", currency: "USD" });
}

function getNum(x) {
  const n = Number(x);
  return Number.isNaN(n) ? 0 : n;
}

function authorNameForBook(b) {
  const authors = b.authors || [];
  if (authors.length === 0) return "";
  return (authors[0]?.name || "").toLowerCase();
}

function seriesNameForBook(b) {
  const s =
    b.series?.name ||
    b.series_name ||
    b.seriesTitle ||
    b.series ||
    "";
  return String(s || "").toLowerCase();
}

function seriesPosForBook(b) {
  const p = b.series_position ?? b.series_pos ?? b.seriesPosition;
  const n = Number(p);
  return Number.isNaN(n) ? Number.POSITIVE_INFINITY : n;
}

function titleForBook(b) {
  return (b.title || "").toLowerCase();
}

export function sortBooksDefault(books) {
  const arr = [...(books || [])];
  arr.sort((a, b) => {
    const aa = authorNameForBook(a);
    const ab = authorNameForBook(b);
    if (aa < ab) return -1;
    if (aa > ab) return 1;

    const sa = seriesNameForBook(a);
    const sb = seriesNameForBook(b);

    const aHasSeries = sa.trim().length > 0;
    const bHasSeries = sb.trim().length > 0;

    if (aHasSeries && !bHasSeries) return -1;
    if (!aHasSeries && bHasSeries) return 1;

    if (sa < sb) return -1;
    if (sa > sb) return 1;

    const pa = seriesPosForBook(a);
    const pb = seriesPosForBook(b);
    if (pa < pb) return -1;
    if (pa > pb) return 1;

    const ta = titleForBook(a);
    const tb = titleForBook(b);
    if (ta < tb) return -1;
    if (ta > tb) return 1;
    return 0;
  });
  return arr;
}

function buildBooksColumns({ showAuthor, extraColumns }) {
  const cols = [
    {
      label: "Title",
      sortKey: "title",
      className: "whitespace-normal",
      render: (b) => <span className="font-medium text-slate-700">{b.title}</span>,
    },
  ];

  if (showAuthor) {
    cols.push({
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
    });
  }

  cols.push(
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
      render: (b) => {
        const v =
          b.total_author_royalty ??
          b.total_author_royalty_to_date ??
          b.totalRoyalty ??
          0;
        return <span className="tabular-nums">{money(getNum(v))}</span>;
      },
    },
    {
      label: "Paid Author Royalty",
      sortKey: "paid_author_royalty",
      className: "whitespace-nowrap",
      render: (b) => {
        const v =
          b.paid_author_royalty ??
          b.paid_author_royalty_to_date ??
          b.paidRoyalty ??
          0;
        return <span className="tabular-nums">{money(getNum(v))}</span>;
      },
    },
    {
      label: "Unpaid Author Royalty",
      sortKey: "unpaid_author_royalty",
      className: "whitespace-nowrap",
      render: (b) => {
        const v =
          b.unpaid_author_royalty ??
          b.unpaid_author_royalty_to_date ??
          b.unpaidRoyalty ??
          0;
        return <span className="tabular-nums">{money(getNum(v))}</span>;
      },
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
    />
  );
}