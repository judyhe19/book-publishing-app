import { Link } from "react-router-dom";
import React from "react";
import { formatMonthYear } from "../../../shared/utils/dateUtils";

// Sort configuration
// IMPORTANT: Keep sortKeys in sync with backend: bookapp/views/sales.py (FIELD_MAP)
export const SORT_CONFIG = {
    DEFAULT_FIELD: 'date',
    DEFAULT_ORDER: '-date',
    // Fields that should default to descending on first click
    DESC_FIELDS: ['date', 'quantity', 'publisher_revenue', 'publisher_revenue_original', 'total_royalties'],
};

export const TABLE_COLUMNS = [
    {
        label: 'Book Title',
        sortKey: 'book_title',
        className: 'w-[10%] overflow-hidden text-ellipsis',
        render: (sale) => (
            <Link
                to={`/books/${sale.book}`}
                className="font-medium text-blue-600 hover:text-blue-800 hover:underline"
                onClick={(e) => e.stopPropagation()}
                title={sale.book_title}
            >
                {sale.book_title}
            </Link>
        ),
    },
    {
        label: 'Author',
        sortKey: 'authors',
        className: 'w-[7%] overflow-hidden text-ellipsis',
        render: (sale) => {
            const name = sale.author_names?.[0];
            if (!name) return <span className="text-gray-400">—</span>;
            return <span className="font-medium" title={name}>{name}</span>;
        },
    },
    {
        label: 'Date',
        sortKey: 'date',
        className: 'w-[5%] whitespace-nowrap',
        render: (sale) => {
            return formatMonthYear(sale.date);
        },
    },
    {
        label: 'Qty/KENP',
        sortKey: 'quantity',
        type: 'number',
        className: 'w-[5%] whitespace-nowrap',
        render: (sale) => {
            if (sale.format === "kindle unlimited" && sale.kenp != null) {
                return `${sale.kenp} Pg`;
            }
            return sale.quantity != null ? sale.quantity : <span className="text-gray-400">—</span>;
        },
    },
    {
        label: 'Revenue (Orig)',
        sortKey: 'publisher_revenue_original',
        type: 'number',
        className: 'w-[7%] whitespace-nowrap',
        render: (sale) => {
            if (sale.publisher_revenue_original != null) {
                return `${sale.publisher_revenue_original} ${sale.currency || 'USD'}`;
            }
            return <span className="text-gray-400">—</span>;
        },
    },
    {
        label: 'Revenue (USD)',
        sortKey: 'publisher_revenue',
        type: 'number',
        className: 'w-[7%] whitespace-nowrap',
        render: (sale) => {
            return sale.publisher_revenue ? `$${sale.publisher_revenue}` : '$0.00';
        },
    },
    {
        label: 'Author\nRoyalty',
        sortKey: 'author_royalty',
        type: 'number',
        className: 'w-[5%] whitespace-nowrap',
        render: (sale) => <span className="font-medium">${Number(sale.author_royalty || 0).toFixed(2)}</span>,
    },
    {
        label: 'Source',
        sortKey: 'sale_source',
        className: 'w-[5%]',
        render: (sale) => {
            const label = sale.sale_source === 'handsold' ? 'Handsold' : 'Distributor';
            const color = sale.sale_source === 'handsold'
                ? 'bg-purple-100 text-purple-700'
                : 'bg-blue-100 text-blue-700';
            return (
                <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${color}`}>
                    {label}
                </span>
            );
        },
    },
    {
        label: 'Distributor',
        sortKey: 'distributor',
        className: 'w-[5%] overflow-hidden text-ellipsis',
        render: (sale) => {
            if (!sale.distributor) return <span className="text-gray-400">—</span>;
            return <span title={sale.distributor}>{sale.distributor}</span>;
        },
    },
    {
        label: 'Format',
        sortKey: 'format',
        className: 'w-[5%] overflow-hidden text-ellipsis',
        render: (sale) => {
            if (!sale.format) return <span className="text-gray-400">—</span>;
            const formatted = sale.format.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
            return <span title={formatted}>{formatted}</span>;
        },
    },
    {
        label: 'Comment',
        sortKey: 'comment',
        className: 'w-[10%] overflow-hidden text-ellipsis',
        render: (sale) => (
            <span className="text-sm text-gray-600" title={sale.comment || ''}>
                {sale.comment || '—'}
            </span>
        ),
    },
    {
        label: 'Status',
        sortKey: 'paid_status',
        className: 'w-[8%]',
        render: (sale) => {
            if (sale.author_paid) {
                return (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-100 text-green-700 text-xs font-medium">
                        <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                        Paid
                    </span>
                );
            }
            return (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-red-100 text-red-700 text-xs font-medium">
                    <span className="w-1.5 h-1.5 bg-red-500"></span>
                    Unpaid
                </span>
            );
        },
    },
];

// Columns for BookDetailPage — no "Book Title" or "Author" columns
export const BOOK_DETAIL_COLUMNS = TABLE_COLUMNS
    .filter((col) => col.sortKey !== 'book_title' && col.sortKey !== 'authors');
