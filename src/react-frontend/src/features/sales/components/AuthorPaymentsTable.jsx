import React from "react";

function PaymentStatusCell({ paid }) {
  return paid ? (
    <span className="inline-flex items-center gap-2">
      <span className="w-2 h-2 rounded-full bg-green-500 inline-block" />
      <span className="text-xs text-green-700">Paid</span>
    </span>
  ) : (
    <span className="inline-flex items-center gap-2">
      <span className="w-2 h-2 bg-red-500 inline-block" />
      <span className="text-xs text-red-700">Unpaid</span>
    </span>
  );
}

export default function AuthorPaymentsTable({ rows, onGoBook, onGoSale }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Book Title
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Date
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Quantity
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Revenue
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Royalty
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Payment Status
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Actions
            </th>
          </tr>
        </thead>

        <tbody className="bg-white divide-y divide-gray-200">
          {rows.map((r, idx) => (
            <tr key={`${r.sale.id}-${idx}`} className="hover:bg-gray-50">
              <td className="px-6 py-4 text-sm">
                <button
                  className="font-medium text-blue-600"
                  onClick={() => onGoBook(r.sale.book)}
                >
                  {r.sale.book_title}
                </button>
              </td>

              <td className="px-6 py-4 text-sm text-gray-500">
                {new Date(r.sale.date).toLocaleDateString()}
              </td>

              <td className="px-6 py-4 text-sm text-gray-500 text-right">
                {r.sale.quantity}
              </td>

              <td className="px-6 py-4 text-sm text-gray-500 text-right">
                ${r.sale.publisher_revenue}
              </td>

              <td className="px-6 py-4 text-sm text-gray-500 text-right">
                ${r.author.royalty_amount}
              </td>

              <td className="px-6 py-4 text-sm">
                <PaymentStatusCell paid={r.paid} />
              </td>

              <td className="px-6 py-4 text-sm text-right">
                <button
                  className="text-indigo-600 hover:text-indigo-900 font-medium"
                  onClick={() => onGoSale(r.sale.id)}
                >
                  Modify
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
