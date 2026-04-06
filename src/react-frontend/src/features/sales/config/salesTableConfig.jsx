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
        className: 'w-[9%] px-3',
        render: (sale) => {
            return (
                <div className="flex items-center min-w-0 w-full">
                    <Link
                        to={`/books/${sale.book}`}
                        className="font-medium text-blue-600 hover:text-blue-800 hover:underline truncate"
                        onClick={(e) => e.stopPropagation()}
                        title={sale.book_title}
                    >
                        {sale.book_title}
                    </Link>
                    <span className="relative group flex-shrink-0 ml-1 cursor-default" onClick={(e) => e.stopPropagation()}>
                        <svg 
                            xmlns="http://www.w3.org/2000/svg" 
                            viewBox="0 0 20 20" 
                            fill="currentColor" 
                            className={`w-4 h-4 transition-colors ${sale.comment ? 'text-gray-400 group-hover:text-gray-600' : 'text-gray-200 group-hover:text-gray-300'}`}
                        >
                            <path fillRule="evenodd" d="M3.43 2.524A41.29 41.29 0 0110 2c2.236 0 4.43.18 6.57.524 1.437.231 2.43 1.49 2.43 2.902v5.148c0 1.413-.993 2.67-2.43 2.902a41.102 41.102 0 01-3.55.414c-.28.02-.521.18-.643.413l-1.712 3.293a.75.75 0 01-1.33 0l-1.713-3.293a.783.783 0 00-.642-.413 41.108 41.108 0 01-3.55-.414C1.993 13.245 1 11.986 1 10.574V5.426c0-1.413.993-2.67 2.43-2.902z" clipRule="evenodd" />
                        </svg>
                        <span className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max max-w-xs rounded-lg bg-gray-900 text-white text-xs px-3 py-2 opacity-0 group-hover:opacity-100 transition-opacity duration-150 shadow-lg whitespace-pre-wrap z-50 z-[100]">
                            {sale.comment || 'No comment'}
                        </span>
                    </span>
                </div>
            );
        },
    },
    {
        label: 'Author',
        sortKey: 'authors',
        className: 'w-[6%] truncate',
        render: (sale) => {
            const name = sale.author_names?.[0];
            if (!name) return <span className="text-gray-400">—</span>;
            return <span className="font-medium" title={name}>{name}</span>;
        },
    },
    {
        label: 'Date',
        sortKey: 'date',
        className: 'w-[3%] truncate',
        render: (sale) => {
            return formatMonthYear(sale.date, "", true);
        },
    },
    {
        label: 'Status',
        sortKey: 'paid_status',
        className: 'w-[3%] truncate',
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
    {
        label: (
            <div className="flex flex-col leading-tight">
                <span>Qty /</span>
                <span>KENP</span>
            </div>
        ),
        sortKey: 'quantity',
        type: 'number',
        className: 'w-[1.5%] truncate',
        render: (sale) => {
            if (sale.format === "kindle unlimited" && sale.kenp != null) {
                return `${sale.kenp} Pg`;
            }
            return sale.quantity != null ? sale.quantity : <span className="text-gray-400">—</span>;
        },
    },
    {
        label: 'Pub Rev',
        sortKey: 'publisher_revenue',
        type: 'number',
        className: 'w-[3%] min-w-0 px-3',
        render: (sale) => {
            const origRev = sale.publisher_revenue_original != null ? sale.publisher_revenue_original : sale.publisher_revenue;
            const currency = sale.currency || 'USD';
            const usdRev = sale.publisher_revenue ? sale.publisher_revenue : '0.00';
            
            return (
                <div className="flex flex-col text-xs leading-snug">
                    <span className="font-medium text-gray-900 truncate" title={`${origRev} ${currency}`}>{origRev} {currency}</span>
                    {currency !== 'USD' ? (
                        <span className="text-gray-500 truncate mt-0.5" title={`$${usdRev} USD`}>${usdRev} USD</span>
                    ) : (
                        <span className="text-gray-400 mt-0.5 truncate opacity-50 select-none">-</span>
                    )}
                </div>
            );
        },
    },
    {
        label: 'Royalty',
        sortKey: 'author_royalty',
        type: 'number',
        className: 'w-[3%] truncate',
        render: (sale) => <span className="font-medium" title={`$${Number(sale.author_royalty || 0).toFixed(2)}`}>${Number(sale.author_royalty || 0).toFixed(2)}</span>,
    },
    {
        label: 'Source',
        sortKey: 'sale_source',
        className: 'w-[3%] truncate',
        render: (sale) => {
            const label = sale.sale_source === 'handsold' ? 'Handsold' : 'Distributor';
            const color = sale.sale_source === 'handsold'
                ? 'bg-purple-100 text-purple-700'
                : 'bg-blue-100 text-blue-700';
            return (
                <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${color}`} title={label}>
                    {label}
                </span>
            );
        },
    },
    {
        label: 'Distributor',
        sortKey: 'distributor',
        className: 'w-[4%] truncate',
        render: (sale) => {
            if (!sale.distributor) return <span className="text-gray-400">—</span>;
            return <span title={sale.distributor}>{sale.distributor}</span>;
        },
    },
    {
        label: 'Format',
        sortKey: 'format',
        className: 'w-[4%] truncate',
        render: (sale) => {
            if (!sale.format) return <span className="text-gray-400">—</span>;
            const FORMAT_DISPLAY = { print: 'Print', ebook: 'eBook', 'kindle unlimited': 'Kindle Unlimited' };
            const formatted = FORMAT_DISPLAY[sale.format] || sale.format;
            return <span title={formatted}>{formatted}</span>;
        },
    },

];

// Columns for BookDetailPage — no "Book Title" or "Author" columns
export const BOOK_DETAIL_COLUMNS = TABLE_COLUMNS
    .filter((col) => col.sortKey !== 'book_title' && col.sortKey !== 'authors');
