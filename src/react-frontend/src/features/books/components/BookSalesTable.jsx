// src/features/books/components/BookSalesTable.jsx
import React from "react";
import { DataTable, PaymentStatusBadge } from "../../../shared/components";

const BOOK_SALES_COLUMNS = [
  {
    label: "Author",
    sortKey: "authors",
    render: (sale) => {
      const name = sale.author_names?.[0];
      return name
        ? <span className="font-medium">{name}</span>
        : <span className="text-gray-400">—</span>;
    },
  },
  {
    label: "Date",
    sortKey: "date",
    render: (sale) => {
      const [year, month] = sale.date.split("-").map(Number);
      const date = new Date(year, month - 1);
      return date.toLocaleDateString("en-US", {
        month: "long",
        year: "numeric",
      });
    },
  },
  {
    label: "Quantity",
    sortKey: "quantity",
    render: (sale) => sale.quantity,
  },
  {
    label: "Revenue",
    sortKey: "publisher_revenue",
    render: (sale) => `$${Number(sale.publisher_revenue).toFixed(2)}`,
  },
  {
    label: "Royalty",
    sortKey: "author_royalty",
    render: (sale) => (
      <span className="font-medium">${Number(sale.author_royalty).toFixed(2)}</span>
    ),
  },
  {
    label: "Status",
    sortKey: "author_paid",
    render: (sale) => (
      <PaymentStatusBadge status={sale.author_paid ? "paid" : "unpaid"} />
    ),
  },
  {
    label: "Actions",
    type: "actions",
    getActions: (sale) => [
      { label: "Modify", to: `/sale/${sale.id}`, variant: "primary" },
    ],
  },
];

export default function BookSalesTable({ data, loading, ordering, onSort }) {
  return (
    <DataTable
      data={data}
      columns={BOOK_SALES_COLUMNS}
      loading={loading}
      ordering={ordering}
      onSort={onSort}
      emptyMessage="No sales records found for this book."
      loadingMessage="Loading sales data..."
    />
  );
}