/**
 * Format a book label with title, ISBN-13, and optionally ASIN
 * @param {string} title - Book title
 * @param {string} isbn13 - ISBN-13
 * @param {string} [asin] - Optional ASIN
 * @returns {string} - Formatted label
 */
export function formatBookLabel(title, isbn13, asin) {
    if (asin) {
        return `${title} (ISBN-13: ${isbn13}, ASIN: ${asin})`;
    }
    return `${title} (ISBN-13: ${isbn13})`;
}
