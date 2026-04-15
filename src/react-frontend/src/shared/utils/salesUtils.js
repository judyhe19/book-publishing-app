/**
 * Shared utilities for sales data handling
 */

export const EMPTY_ROW = {
    date: '',
    book: null,
    format: 'print',
    quantity: '',
    kenp: '',
    sale_source: 'distributor',
    distributor: 'Other',
    currency: 'USD',
    publisher_revenue: '',
    publisher_revenue_original: '',
    author_royalty: '',
    author_paid: false,
    comment: '',
};

/**
 * Transforms a row from UI format to API format
 */
export const transformRowToSaleData = (row) => {
    const isKU = row.format === 'kindle unlimited';
    const base = {
        book: row.book ? row.book.value : null,
        date: row.date,
        format: row.format || null,
        quantity: isKU ? null : (parseInt(row.quantity) || null),
        kenp: isKU ? (parseInt(row.kenp) || null) : null,
        sale_source: row.sale_source,
        distributor: row.distributor || null,
        currency: row.currency || 'USD',
        author_royalty: parseFloat(row.author_royalty || 0),
        author_paid: Boolean(row.author_paid),
        comment: row.comment || '',
    };
    
    if (base.sale_source === 'distributor') {
        if (base.currency !== 'USD') {
            base.publisher_revenue_original = parseFloat(row.publisher_revenue_original);
        } else {
            const usdRevenue = parseFloat(row.publisher_revenue);
            base.publisher_revenue = usdRevenue;
            base.publisher_revenue_original = usdRevenue;
        }
    } else {
        base.publisher_revenue = parseFloat(row.publisher_revenue);
    }
    
    return base;
};

/**
 * Checks if a row has any data entered (partially or fully filled)
 */
export const isRowStarted = (row) => {
    return row.date || row.book || row.quantity || row.kenp || row.publisher_revenue || row.publisher_revenue_original;
};

/**
 * Checks if a row has all required fields filled
 */
export const isRowComplete = (row) => {
    return row.book && row.quantity && row.publisher_revenue && row.date && row.sale_source;
};

/**
 * Computes author royalty based on sale source and book data.
 *
 * @param {string} saleSource - 'distributor', 'handsold', or 'kickstarter'
 * @param {number} publisherRevenue - the publisher revenue amount
 * @param {Object} book - the selected book option (from AsyncSelect)
 * @returns {string} computed royalty as a fixed-2 string, or ''
 */
export const computeAuthorRoyalty = (saleSource, publisherRevenue, book) => {
    const revenue = Number(publisherRevenue);
    if (Number.isNaN(revenue) || !revenue || !book) return '';

    const rate = (saleSource === 'handsold' || saleSource === 'kickstarter')
        ? Number(book.hand_sold_author_royalty_rate) 
        : Number(book.distributor_author_royalty_rate);
        
    if (Number.isNaN(rate)) return '';

    return (rate * revenue).toFixed(2);
};

/**
 * Computes publisher revenue for handsold books.
 * Formula: (cover_price - print_cost) × quantity_sold
 *
 * @param {Object} book - the selected book option
 * @param {number|string} quantity - quantity sold
 * @returns {string} computed revenue or '' (placeholder)
 */
export const computeHandsoldRevenue = (book, quantity) => {
    const coverPrice = Number(book?.cover_price ?? 0);
    const printCost = Number(book?.print_cost ?? 0);
    const qty = Number(quantity);
    if (!coverPrice || Number.isNaN(qty) || qty < 1) return '';
    return ((coverPrice - printCost) * qty).toFixed(2);
};

/**
 * Formats a YYYY-MM string into "Month Year" format (e.g., "January 2026").
 * @param {string} dateStr - The YYYY-MM string, e.g. "2026-01"
 * @returns {string} Formatted month and year, or "—" if invalid
 */
export const formatMonthYear = (dateStr) => {
    if (!dateStr) return "—";
    const [year, month] = dateStr.split("-");
    const date = new Date(parseInt(year, 10), parseInt(month, 10) - 1);
    return date.toLocaleString("en-US", { month: "long", year: "numeric" });
};
