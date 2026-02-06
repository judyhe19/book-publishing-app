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

/**
 * Checks if a row has all required fields filled
 */
export const isRowComplete = (row) => {
    return row.book && row.quantity && row.publisher_revenue && row.date;
};

/**
 * Validates a sale row. Returns null if valid, or an error string if invalid.
 */
export const validateSaleRow = (row) => {
    if (!row.book) return "Book is required.";
    if (!row.date) return "Date is required.";
    if (row.quantity === '' || row.quantity === null || row.quantity === undefined) return "Quantity is required.";
    if (row.publisher_revenue === '' || row.publisher_revenue === null || row.publisher_revenue === undefined) return "Revenue is required.";

    const qty = parseInt(row.quantity);
    if (isNaN(qty) || qty <= 0) return "Quantity must be a positive integer.";

    const rev = parseFloat(row.publisher_revenue);
    if (isNaN(rev) || rev < 0) return "Revenue cannot be negative.";

    // Validate Date vs Publication Date
    if (row.book?.publication_date) {
        // Simple string comparison for YYYY-MM works if formats are consistent
        const saleMonth = row.date; // YYYY-MM
        const pubMonth = row.book.publication_date.substring(0, 7); // YYYY-MM
        
        if (saleMonth < pubMonth) {
             return `Sale date cannot be before book publication date (${row.book.publication_date}).`;
        }
    }

    // Validate Royalties
    if (row.author_royalties) {
        for (const [authorId, amount] of Object.entries(row.author_royalties)) {
            const val = parseFloat(amount);
            if (!isNaN(val) && val < 0) {
                // Find author name if possible
                let name = 'Author';
                if (row.book?.authors) {
                    const author = row.book.authors.find(a => String(a.author_id) === String(authorId));
                    if (author) name = author.name;
                }
                return `Royalty for ${name} cannot be negative.`;
            }
        }
    }

    return null;
};




