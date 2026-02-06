/**
 * Format a book label with title and ISBN-13
 * @param {string} title - Book title
 * @param {string} isbn13 - ISBN-13
 * @returns {string} - Formatted label "Title (ISBN-13: xxx)"
 */
export function formatBookLabel(title, isbn13) {
    return `${title} (ISBN-13: ${isbn13})`;
}
