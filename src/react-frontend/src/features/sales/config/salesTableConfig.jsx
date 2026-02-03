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
        sortValue: (sale) => sale.author_details?.map(a => a.name).join(', ') || '', // sort by each book's first author's names
        render: (sale) => {
            const authors = sale.author_details || [];
            if (authors.length === 0) {
                return Object.keys(sale.author_royalties || {}).length > 0
                    ? <span className="text-gray-500 italic">Authors (IDs only)</span>
                    : <span className="text-gray-400">-</span>;
            }

            return (
                <div className="flex flex-col">
                    {authors.map((auth, idx) => (
                        <div key={idx} className="whitespace-nowrap font-medium">
                            {auth.name}
                        </div>
                    ))}
                </div>
            );
        },
    },
    {
        label: 'Date',
        sortKey: 'date',
        render: (sale) => new Date(sale.date).toLocaleDateString(),
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
        label: 'Royalties',
        sortKey: 'total_royalties',
        type: 'number',
        sortValue: (sale) => sale.author_details?.reduce((sum, a) => sum + Number(a.royalty_amount), 0) || 0, // sort by each book's total royalties
        render: (sale) => (
            <div className="flex flex-col gap-1">
                {sale.author_details && sale.author_details.map((auth, idx) => (
                    <div key={idx} className="font-medium text-right">
                        ${auth.royalty_amount}
                    </div>
                ))}
            </div>
        ),
    },
    {
        label: 'Payment Status',
        sortKey: 'paid_status',
        sortValue: (sale) => sale.author_details && sale.author_details.every(a => a.paid), // true if all authors have been paid, false otherwise
        render: (sale) => (
            <div className="flex flex-col gap-1">
                {sale.author_details && sale.author_details.map((auth, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                        {auth.paid ? (
                            <div className="flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-green-500 inline-block"></span>
                                <span className="text-xs text-green-700">Paid</span>
                            </div>
                        ) : (
                            <div className="flex items-center gap-1">
                                <span className="w-2 h-2 bg-red-500 inline-block"></span>
                                <span className="text-xs text-red-700">Unpaid</span>
                            </div>
                        )}
                    </div>
                ))}
            </div>
        ),
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
