// src/features/sales/components/AuthorPaymentsTable.jsx
import React from "react";
import { formatMonthYear } from "../../../shared/utils/dateUtils";
import { DataTable, PaymentStatusBadge } from "../../../shared/components";

const getColumns = (onGoBook) => [
  {
    label: "Book Title",
    render: (r) => (
      <button
        className="font-medium text-blue-600"
        onClick={(e) => { e.stopPropagation(); onGoBook(r.sale.book); }}
      >
        {r.sale.book_title}
      </button>
    ),
  },
  {
    label: "Date",
    render: (r) => formatMonthYear(r.sale.date),
  },
  {
    label: "Quantity",
    className: "text-right whitespace-nowrap",
    render: (r) => r.sale.quantity,
  },
  {
    label: "Revenue",
    className: "text-right whitespace-nowrap",
    render: (r) => `$${r.sale.publisher_revenue}`,
  },
  {
    label: "Royalty",
    className: "text-right whitespace-nowrap",
    render: (r) => `$${r.author.royalty_amount}`,
  },
  {
    label: "Payment Status",
    render: (r) => (
      <PaymentStatusBadge status={r.paid ? "paid" : "unpaid"} variant="badge" />
    ),
  },
];

export default function AuthorPaymentsTable({ rows, onGoBook, onGoSale }) {
  const columns = React.useMemo(
    () => getColumns(onGoBook),
    [onGoBook]
  );

  // DataTable uses `row.id` for the key, so we need to inject an id
  const dataWithId = rows.map((r, idx) => ({
    ...r,
    id: `${r.sale?.id}-${idx}`,
  }));

  return (
    <DataTable
      data={dataWithId}
      columns={columns}
      onRowClick={(r) => onGoSale(r.sale.id)}
      emptyMessage="No author payments found."
    />
  );
}
