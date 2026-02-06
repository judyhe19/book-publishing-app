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


// GET /authors/
export function listAuthors() {
  return apiFetch("/api/authors/");
}

// POST /authors/  body: { name }
export function createAuthor(name) {
  return apiFetch("/api/authors/", {
    method: "POST",
    body: { name },
  });
}

// POST /books/  body matches BookCreateSerializer
export function createBook(payload) {
  return apiFetch("/api/books/", {
    method: "POST",
    body: payload,
  });
}
