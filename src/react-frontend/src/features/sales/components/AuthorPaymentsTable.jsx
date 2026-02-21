// src/features/sales/components/AuthorPaymentsTable.jsx
import React from "react";
import { formatMonthYear } from "../../../shared/utils/dateUtils";
import { DataTable, PaymentStatusBadge } from "../../../shared/components";

const getColumns = (onGoBook, onGoSale) => [
  {
    label: "Book Title",
    render: (r) => (
      <button
        className="font-medium text-blue-600"
        onClick={() => onGoBook(r.sale.book)}
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
  {
    label: "Actions",
    className: "text-right whitespace-nowrap",
    type: "actions",
    getActions: (r) => [
      { label: "Modify", onClick: () => onGoSale(r.sale.id), variant: "primary" },
    ],
  },
];

export default function AuthorPaymentsTable({ rows, onGoBook, onGoSale }) {
  const columns = React.useMemo(
    () => getColumns(onGoBook, onGoSale),
    [onGoBook, onGoSale]
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
      emptyMessage="No author payments found."
    />
  );
}
