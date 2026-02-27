// src/features/books/components/BooksTable.jsx
import { DataTable } from "../../../shared/components";
import { formatMonthYear } from "../../../shared/utils/dateUtils";

const BOOKS_COLUMNS = [
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
    className: "whitespace-normal",
    render: (b) => <span className="font-medium text-slate-700">{b.title}</span>,
  },
  {
    label: "Author",
    sortKey: "author_name",
    className: "whitespace-nowrap",
    render: (b) => (
      <span className="text-slate-700">{b.author_name || <span className="text-slate-400">—</span>}</span>
    ),
  },
  {
    label: "Series",
    sortKey: "series_name",
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
    render: (b) => <span className="font-mono text-slate-700">{b.isbn_13 || "—"}</span>,
  },
  {
    label: "Publication",
    sortKey: "publication_date",
    render: (b) => formatMonthYear(b.publication_date),
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
