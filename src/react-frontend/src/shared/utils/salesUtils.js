/**
 * Shared utilities for sales data handling
 */

export const EMPTY_ROW = {
    date: '',
    book: null,
    quantity: '',
    sale_source: 'distributor',
    publisher_revenue: '',
    author_royalty: '',
    author_paid: false,
    comment: '',
};

/**
 * Transforms a row from UI format to API format
 */
export const transformRowToSaleData = (row) => {
    return {
        book: row.book ? row.book.value : null,
        date: row.date,
        quantity: parseInt(row.quantity),
        sale_source: row.sale_source,
        publisher_revenue: parseFloat(row.publisher_revenue),
        author_royalty: parseFloat(row.author_royalty || 0),
        author_paid: row.author_paid || false,
        comment: row.comment || '',
    };
};

/**
 * Checks if a row has any data entered (partially or fully filled)
 */
export const isRowStarted = (row) => {
    return row.date || row.book || row.quantity || row.publisher_revenue;
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
 * TODO: Once the Book model has dedicated `distributor_royalty_rate`
 *       and `hand_sold_royalty_rate` fields, use those instead of
 *       `authors[0].royalty_rate`.
 *
 * @param {string} saleSource - 'distributor' or 'handsold'
 * @param {number} publisherRevenue - the publisher revenue amount
 * @param {Object} book - the selected book option (from AsyncSelect)
 * @returns {string} computed royalty as a fixed-2 string, or ''
 */
export const computeAuthorRoyalty = (saleSource, publisherRevenue, book) => {
    const revenue = Number(publisherRevenue);
    if (Number.isNaN(revenue) || !revenue) return '';

    // TODO: Use book.distributor_royalty_rate or book.hand_sold_royalty_rate
    //       based on saleSource once those fields exist on the Book model.
    const rate = Number(book?.authors?.[0]?.royalty_rate ?? 0);
    if (Number.isNaN(rate)) return '';

    return (rate * revenue).toFixed(2);
};

/**
 * Computes publisher revenue for handsold books.
 * Formula: (cover_price - print_cost) × quantity_sold
 *
 * TODO: Once the Book model has `cover_price` and `print_cost`,
 *       compute as: (cover_price - print_cost) × quantity.
 *       For now returns a placeholder empty string.
 *
 * @param {Object} book - the selected book option
 * @param {number|string} quantity - quantity sold
 * @returns {string} computed revenue or '' (placeholder)
 */
export const computeHandsoldRevenue = (/* book, quantity */) => {
    // TODO: Uncomment once Book model has cover_price and print_cost:
    // const coverPrice = Number(book?.cover_price ?? 0);
    // const printCost = Number(book?.print_cost ?? 0);
    // const qty = Number(quantity);
    // if (!coverPrice || Number.isNaN(qty) || !qty) return '';
    // return ((coverPrice - printCost) * qty).toFixed(2);
    return '';
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
