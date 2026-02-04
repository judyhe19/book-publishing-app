// src/features/books/api/booksApi.js
import { apiFetch } from "../../../shared/api/http";

/**
 * GET /api/books/?page=&page_size=&q=&ordering=
 * Backend returns:
 * {
 *   count, page, page_size, total_pages, results: [...]
 * }
 */
export function getBooks(queryParams = "") {
  const qs = queryParams ? `?${queryParams}` : "";
  return apiFetch(`/api/books/${qs}`);
}
