import { Link } from "react-router-dom";
import React from "react";

// Sort configuration
// IMPORTANT: Keep sortKeys in sync with backend: bookapp/views/sales.py (FIELD_MAP)
export const SORT_CONFIG = {
    DEFAULT_FIELD: 'date',
    DEFAULT_ORDER: '-date',
    // Fields that should default to descending on first click
    DESC_FIELDS: ['date', 'quantity', 'publisher_revenue', 'total_royalties'],
};

export const TABLE_COLUMNS = [
    {
        label: 'Book Title',
        sortKey: 'book_title',
        render: (sale) => (
            <Link to={`/books/${sale.book}`} className="font-medium text-blue-600">
                {sale.book_title}
            </Link>
        ),
    },
    {
        label: 'Author(s)',
        sortKey: 'authors',
        sortValue: (sale) => sale.author_details?.[0]?.name || '', // sort by first author's name
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
        type: 'number',
        render: (sale) => sale.quantity,
    },
    {
        label: 'Revenue',
        sortKey: 'publisher_revenue',
        type: 'number',
        render: (sale) => `$${sale.publisher_revenue}`,
    },
    {
        label: 'Total Royalties',
        sortKey: 'total_royalties',
        type: 'number',
        sortValue: (sale) => sale.author_details?.reduce((sum, a) => sum + Number(a.royalty_amount), 0) || 0,
        render: (sale) => {
            const total = sale.author_details?.reduce((sum, a) => sum + Number(a.royalty_amount), 0) || 0;
            return <span className="font-medium">${total.toFixed(2)}</span>;
        },
    },
    {
        label: 'Status',
        sortKey: 'paid_status',
        sortValue: (sale) => {
            const authors = sale.author_details || [];
            if (authors.length === 0) return 2; // Treat no authors as unpaid
            const paidCount = authors.filter(a => a.paid).length;
            if (paidCount === authors.length) return 0; // Fully Paid
            if (paidCount > 0) return 1; // Partially Paid
            return 2; // Unpaid
        },
        render: (sale) => {
            const authors = sale.author_details || [];
            const paidCount = authors.filter(a => a.paid).length;
            const totalCount = authors.length;
            
            // Fully Paid: all authors are paid
            if (totalCount > 0 && paidCount === totalCount) {
                return (
                    <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full bg-green-100 text-green-700 text-xs font-medium">
                        <span className="w-2 h-2 rounded-full bg-green-500"></span>
                        Fully Paid
                    </span>
                );
            }
            
            // Partially Paid: some authors are paid
            if (paidCount > 0) {
                return (
                    <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full bg-amber-100 text-amber-700 text-xs font-medium">
                        <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                        Partially Paid
                    </span>
                );
            }
            
            // Unpaid: no authors are paid
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
                to={`/sale/${sale.id}/edit`}
                className="text-indigo-600 hover:text-indigo-900 font-medium"
            >
                Modify
            </Link>
        ),
    },
];
