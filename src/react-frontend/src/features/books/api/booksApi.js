// src/features/books/api/booksApi.js
import { apiFetch } from "../../../shared/api/http";

/**
 * GET /api/books/?page=&page_size=&q=&ordering=
 * Backend returns:
 * {
 *   count, page, page_size, total_pages, results: [...]
 * }
 */

// LIST
export function getBooks(queryParams = "") {
  const qs = queryParams ? `?${queryParams}` : "";
  return apiFetch(`/api/books/${qs}`);
}

// AUTHORS
export function listAuthors() {
  return apiFetch("/api/authors/");
}

export function createAuthor(name) {
  return apiFetch("/api/authors/", {
    method: "POST",
    body: { name },
  });
}

// BOOK CRUD
export function getBook(bookId) {
  return apiFetch(`/api/books/${bookId}/`);
}

export function updateBook(bookId, payload) {
  return apiFetch(`/api/books/${bookId}/`, {
    method: "PATCH",
    body: payload,
  });
}

export function deleteBook(bookId) {
  return apiFetch(`/api/books/${bookId}/`, {
    method: "DELETE",
  });
}

export function createBook(payload) {
  return apiFetch("/api/books/", {
    method: "POST",
    body: payload,
  });
}

// ✅ NEW: totals for Book Detail page sales summary cards
export function getBookSalesTotals(bookId) {
  return apiFetch(`/api/sale/book/${bookId}/totals`);
}
