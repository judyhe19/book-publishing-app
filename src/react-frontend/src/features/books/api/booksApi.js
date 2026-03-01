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
export async function listAuthors() {
  const data = await apiFetch("/api/authors/");
  // API returns paginated response, extract the results array
  return Array.isArray(data) ? data : (data.results || []);
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

// SERIES
export function listSeries() {
  return apiFetch("/api/series/");
}

export function reorderSeries(seriesName, bookIds) {
  return apiFetch("/api/series/reorder/", {
    method: "POST",
    body: { series_name: seriesName, book_ids: bookIds },
  });
}

export function getBookSalesTotals(bookId) {
  return apiFetch(`/api/sales/book/${bookId}/totals`);
}
/**
 * Upload a cover image file.
 * @param {File} file - The image file to upload
 * @returns {Promise<{cover_image_path: string}>} - The path to use in book data
 */
export async function uploadCoverImage(file) {
  // Ensure CSRF cookie is set
  await fetch("/api/csrf", { credentials: "include" });

  // Get CSRF token from cookie
  const csrfToken = document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];

  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('/api/books/upload-cover/', {
    method: 'POST',
    body: formData,
    credentials: 'include',
    headers: {
      'X-CSRFToken': csrfToken,
    },
    // Note: Don't set Content-Type - browser sets it automatically with boundary for FormData
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.error || 'Failed to upload image');
  }

  return response.json();
}