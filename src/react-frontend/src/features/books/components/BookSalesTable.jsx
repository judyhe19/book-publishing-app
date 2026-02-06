import React from 'react';
import { Link } from 'react-router-dom';
import { Spinner } from "../../../shared/components/Spinner";

// Table columns for book sales (excludes Book Title since we're already on the book page)
const BOOK_SALES_COLUMNS = [
    {
        label: 'Author(s)',
        sortKey: 'authors',
        render: (sale) => {
            const authors = sale.author_details || [];
            if (authors.length === 0) {
                return Object.keys(sale.author_royalties || {}).length > 0
                    ? <span className="text-gray-500 italic">Authors (IDs only)</span>
                    : <span className="text-gray-400">-</span>;
            }

            return (
                <div className="flex flex-col gap-2">
                    {authors.map((auth, idx) => (
                        <div key={idx} className="flex items-center justify-between gap-4">
                            <span className="font-medium whitespace-nowrap">{auth.name}</span>
                            <div className="flex items-center gap-2">
                                <span className="text-sm text-gray-600">${auth.royalty_amount}</span>
                                {auth.paid ? (
                                    <span className="w-2 h-2 rounded-full bg-green-500" title="Paid"></span>
                                ) : (
                                    <span className="w-2 h-2 bg-red-500" title="Unpaid"></span>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            );
        },
    },
    {
        label: 'Date',
        sortKey: 'date',
        render: (sale) => {
            const [year, month] = sale.date.split('-').map(Number);
            const date = new Date(year, month - 1);
            return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
        },
    },
    {
        label: 'Quantity',
        sortKey: 'quantity',
        render: (sale) => sale.quantity,
    },
    {
        label: 'Revenue',
        sortKey: 'publisher_revenue',
        render: (sale) => `$${sale.publisher_revenue}`,
    },
    {
        label: 'Total Royalties',
        sortKey: 'total_royalties',
        render: (sale) => {
            const total = sale.author_details?.reduce((sum, a) => sum + Number(a.royalty_amount), 0) || 0;
            return <span className="font-medium">${total.toFixed(2)}</span>;
        },
    },
    {
        label: 'Status',
        sortKey: 'paid_status',
        render: (sale) => {
            const authors = sale.author_details || [];
            const paidCount = authors.filter(a => a.paid).length;
            const totalCount = authors.length;
            
            if (totalCount > 0 && paidCount === totalCount) {
                return (
                    <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full bg-green-100 text-green-700 text-xs font-medium">
                        <span className="w-2 h-2 rounded-full bg-green-500"></span>
                        Fully Paid
                    </span>
                );
            }
            
            if (paidCount > 0) {
                return (
                    <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full bg-amber-100 text-amber-700 text-xs font-medium">
                        <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                        Partially Paid
                    </span>
                );
            }
            
            return (
                <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full bg-red-100 text-red-700 text-xs font-medium">
                    <span className="w-2 h-2 rounded-full bg-red-500"></span>
                    Unpaid
                </span>
            );
        },
    },
    {
        label: 'Actions',
        render: (sale) => (
            <Link
                to={`/sale/${sale.id}`}
                className="text-indigo-600 hover:text-indigo-900 font-medium"
            >
                Modify
            </Link>
        ),
    },
];

export default function BookSalesTable({ data, loading, ordering, onSort }) {

    const renderSortIcon = (field) => {
        if (!field) return null;
        if (ordering === field) return " ↑";
        if (ordering === `-${field}`) return " ↓";
        return "";
    };

    return (
        <div className="overflow-x-auto rounded-lg border border-slate-200">
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                        {BOOK_SALES_COLUMNS.map((col, idx) => (
                            <th
                                key={idx}
                                onClick={col.sortKey ? () => onSort(col.sortKey) : undefined}
                                className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${col.sortKey ? 'cursor-pointer hover:bg-gray-100' : ''}`}
                            >
                                {col.label} {renderSortIcon(col.sortKey)}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {loading ? (
                        <tr>
                            <td colSpan={BOOK_SALES_COLUMNS.length} className="px-6 py-12 text-center">
                                <div className="flex justify-center items-center gap-2 text-slate-500">
                                    <Spinner />
                                    <span>Loading sales data...</span>
                                </div>
                            </td>
                        </tr>
                    ) : data.length === 0 ? (
                        <tr>
                            <td colSpan={BOOK_SALES_COLUMNS.length} className="px-6 py-4 text-center text-slate-500">
                                No sales records found for this book.
                            </td>
                        </tr>
                    ) : (
                        data.map((sale) => (
                            <tr key={sale.id} className="hover:bg-gray-50">
                                {BOOK_SALES_COLUMNS.map((col, idx) => (
                                    <td key={idx} className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {col.render(sale)}
                                    </td>
                                ))}
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
}
