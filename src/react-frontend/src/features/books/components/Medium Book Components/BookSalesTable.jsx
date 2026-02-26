// src/features/books/components/BookSalesTable.jsx
import React from "react";
import { DataTable, PaymentStatusBadge } from "../../../shared/components";

function getPaymentStatus(sale) {
  const authors = sale.author_details || [];
  const paidCount = authors.filter((a) => a.paid).length;
  const totalCount = authors.length;

  if (totalCount > 0 && paidCount === totalCount) return "success";
  if (paidCount > 0) return "partial";
  return "unpaid";
}

const BOOK_SALES_COLUMNS = [
  {
    label: "Author",
    sortKey: "authors",
    render: (sale) => {
      const authors = sale.author_details || [];

      if (authors.length === 0) {
        return <span className="text-gray-400">-</span>;
      }

      return (
        <div className="flex flex-col gap-2">
          {authors.map((auth, idx) => (
            <div key={idx} className="flex items-center justify-between gap-4">
              <span className="font-medium whitespace-nowrap">
                {auth.name}
              </span>
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">
                  ${auth.royalty_amount}
                </span>
                <PaymentStatusBadge
                  status={auth.paid ? "paid" : "unpaid"}
                  variant="dot"
                />
              </div>
            </div>
          ))}
        </div>
      );
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
    render: (sale) => `$${sale.publisher_revenue}`,
  },
  {
    label: "Total Royalties",
    sortKey: "total_royalties",
    render: (sale) => {
      const total =
        sale.author_details?.reduce(
          (sum, a) => sum + Number(a.royalty_amount),
          0
        ) || 0;
      return <span className="font-medium">${total.toFixed(2)}</span>;
    },
  },
  {
    label: "Status",
    sortKey: "paid_status",
    render: (sale) => (
      <PaymentStatusBadge status={getPaymentStatus(sale)} />
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

export default function BookSalesTable({
  data,
  loading,
  ordering,
  onSort,
}) {
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