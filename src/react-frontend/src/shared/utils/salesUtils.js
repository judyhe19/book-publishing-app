/**
 * Shared utilities for sales data handling
 */

export const EMPTY_ROW = {
    date: '',
    book: null,
    quantity: '',
    publisher_revenue: '',
    author_royalties: {},
    author_paid: {}
};

/**
 * Transforms a row from UI format to API format
 */
export const transformRowToSaleData = (row) => {
    const sale = {
        book: row.book ? row.book.value : null,
        date: `${row.date}-01`,
        quantity: parseInt(row.quantity),
        publisher_revenue: parseFloat(row.publisher_revenue),
        author_royalties: {},
        author_paid: {}
    };

    const royaltyInput = row.author_royalties || {};
    const paidInput = row.author_paid || {};
    const authors = row.book?.authors || [];

    authors.forEach(author => {
        const amount = royaltyInput[author.author_id];
        if (amount !== undefined && amount !== '') {
            sale.author_royalties[author.author_id] = parseFloat(amount);
        }
        if (paidInput[author.author_id]) {
            sale.author_paid[author.author_id] = true;
        }
    });

    return sale;
};

/**
 * Checks if a row has any data entered (partially or fully filled)
 */
export const isRowStarted = (row) => {
    return row.date || row.book || row.quantity || row.publisher_revenue;
};






