// src/features/sales/components/AuthorPaymentsTable.jsx
import React from "react";
import { Link } from "react-router-dom";
import { formatMonthYear } from "../../../shared/utils/dateUtils";
import { DataTable, PaymentStatusBadge } from "../../../shared/components";

const getColumns = () => [
  {
    label: "Book Title",
    render: (r) => (
      <Link
        to={`/books/${r.sale.book}`}
        className="font-medium text-blue-600 underline hover:text-blue-800"
        onClick={(e) => e.stopPropagation()}
      >
        {r.sale.book_title}
      </Link>
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
  label: "Eligibility",
  render: (r) =>
    r.paid ? (
      <span className="text-slate-500 font-medium">Already Paid</span>
    ) : r.projected ? (
      <span className="text-amber-700 font-medium">Projected</span>
    ) : (
      <span className="text-emerald-700 font-medium">Payable</span>
    ),
},
  {
    label: "Payment Status",
    render: (r) => (
      <PaymentStatusBadge status={r.paid ? "paid" : "unpaid"} variant="badge" />
    ),
  },
];

export default function AuthorPaymentsTable({ rows, onGoSale }) {
  const columns = React.useMemo(
    () => getColumns(),
    []
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
