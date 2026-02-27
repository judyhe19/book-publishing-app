import { Link, useNavigate } from "react-router-dom";
import React from "react";
import { Button } from "../../../shared/components/Button";
import { formatMonthYear } from "../../../shared/utils/dateUtils";

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
            <span className="font-medium text-gray-900">
                {sale.book_title}
            </span>
        ),
    },
    {
        label: 'Author',
        sortKey: 'authors',
        render: (sale) => {
            const name = sale.author_names?.[0];
            if (!name) return <span className="text-gray-400">—</span>;
            return <span className="font-medium whitespace-nowrap">{name}</span>;
        },
    },
    {
        label: 'Date',
        sortKey: 'date',
        render: (sale) => {
            return formatMonthYear(sale.date);
        },
    },
    {
        label: 'Source',
        sortKey: 'sale_source',
        render: (sale) => {
            const label = sale.sale_source === 'handsold' ? 'Handsold' : 'Distributor';
            const color = sale.sale_source === 'handsold'
                ? 'bg-purple-100 text-purple-700'
                : 'bg-blue-100 text-blue-700';
            return (
                <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${color}`}>
                    {label}
                </span>
            );
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
        label: 'Author Royalty',
        sortKey: 'author_royalty',
        type: 'number',
        render: (sale) => <span className="font-medium">${Number(sale.author_royalty || 0).toFixed(2)}</span>,
    },
    {
        label: 'Status',
        sortKey: 'paid_status',
        render: (sale) => {
            if (sale.author_paid) {
                return (
                    <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full bg-green-100 text-green-700 text-xs font-medium">
                        <span className="w-2 h-2 rounded-full bg-green-500"></span>
                        Paid
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
        label: 'Comment',
        sortKey: 'comment',
        render: (sale) => (
            <span className="text-sm text-gray-600 max-w-xs truncate block" title={sale.comment || ''}>
                {sale.comment || '—'}
            </span>
        ),
    },

    {
        label: 'Actions',
        type: 'actions',
        getActions: (sale) => [
            { label: 'Book Details', to: `/books/${sale.book}`, variant: 'secondary' },
            { label: 'Modify Sale', to: `/sale/${sale.id}`, variant: 'primary' }
        ],
    },
];

// Columns for BookDetailPage — no "Book Title" column, no "Book Details" action
export const BOOK_DETAIL_COLUMNS = TABLE_COLUMNS
    .filter((col) => col.sortKey !== 'book_title' && col.sortKey !== 'authors')
    .map((col) => {
        if (col.type === 'actions') {
            return {
                ...col,
                getActions: (sale) =>
                    col.getActions(sale).filter((a) => a.label !== 'Book Details'),
            };
        }
        return col;
    });
