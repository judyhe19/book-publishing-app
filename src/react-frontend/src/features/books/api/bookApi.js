import { apiFetch } from "../../../shared/api/http";

/**
 * Get a single book by ID
 * @param {number} bookId - Book ID
 * @returns {Promise<Object>} - Book data
 */
export function getBook(bookId) {
    return apiFetch(`/api/books/${bookId}/`);
}
