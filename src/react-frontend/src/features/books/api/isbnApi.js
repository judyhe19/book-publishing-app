// src/features/books/api/isbnApi.js
import { apiFetch } from "../../../shared/api/http";

/**
 * Look up book metadata from Google Books by ISBN-10 or ISBN-13.
 * @param {string} isbn
 * @returns {Promise<{title, isbn_13, isbn_10, publication_date, cover_image_url, authors, author_match}>}
 */
export function lookupIsbn(isbn) {
  return apiFetch(`/api/books/isbn-lookup/?isbn=${encodeURIComponent(isbn)}`);
}

/**
 * Download a Google Books cover image and save it to static storage.
 * Should only be called at submit time, not during preview.
 * @param {string} url - The Google Books image URL from lookupIsbn
 * @returns {Promise<{cover_image_path: string}>}
 */
export function downloadCoverFromUrl(url) {
  return apiFetch("/api/books/download-cover/", {
    method: "POST",
    body: { url },
  });
}

/**
 * Returns the backend proxy URL for a Google Books image.
 * Use this as an <img src> to display the cover during the confirmation step
 * without CORS issues. Does not store the image.
 * @param {string} url - The Google Books image URL from lookupIsbn
 * @returns {string}
 */
export function proxyCoverUrl(url) {
  return `/api/books/isbn-lookup/cover/?url=${encodeURIComponent(url)}`;
}
