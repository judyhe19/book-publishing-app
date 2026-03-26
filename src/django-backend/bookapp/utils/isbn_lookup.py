"""
ISBN lookup utility using the Google Books API.

Usage:
    from bookapp.utils.isbn_lookup import IsbnLookup, IsbnLookupError

    lookup = IsbnLookup()
    data = lookup.fetch("9780134685991")   # ISBN-13 or ISBN-10
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"


class IsbnLookupError(Exception):
    """Raised when the Google Books API returns an error or an unexpected response."""


class IsbnLookup:
    """
    Fetches book metadata from the Google Books API by ISBN.

    Accepts either ISBN-13 or ISBN-10. Returns the raw volumeInfo dict
    from the first matching result, plus any industryIdentifiers found.
    """

    def fetch(self, isbn: str) -> dict:
        """
        Look up a book by ISBN and return its volumeInfo from Google Books.

        Args:
            isbn: ISBN-10 or ISBN-13 string (hyphens/spaces are stripped).

        Returns:
            The volumeInfo dict from the first matching Google Books result.

        Raises:
            IsbnLookupError: If no results are found, the API returns an error,
                or the network request fails.
        """
        isbn = isbn.replace("-", "").replace(" ", "").strip()

        response = self._fetch_raw(isbn)
        return self._parse(response, isbn)

    # ──────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────

    def _fetch_raw(self, isbn: str) -> requests.Response:
        params = {"q": f"isbn:{isbn}"}
        api_key = getattr(settings, "GOOGLE_BOOKS_API_KEY", None)
        if api_key:
            params["key"] = api_key

        try:
            response = requests.get(
                GOOGLE_BOOKS_API_URL,
                params=params,
                timeout=10,
            )
        except requests.RequestException as exc:
            raise IsbnLookupError(
                f"Network error while looking up ISBN {isbn}: {exc}"
            ) from exc

        if not response.ok:
            logger.error("Google Books API error for ISBN %s: %s", isbn, response.text)
            raise IsbnLookupError(
                f"Google Books API returned HTTP {response.status_code} for ISBN {isbn}."
            )

        return response

    def _parse(self, response: requests.Response, isbn: str) -> dict:
        try:
            body = response.json()
        except ValueError as exc:
            raise IsbnLookupError(
                f"Invalid JSON response from Google Books API for ISBN {isbn}."
            ) from exc

        if body.get("totalItems", 0) == 0 or "items" not in body:
            raise IsbnLookupError(f"No results found for ISBN {isbn}.")

        try:
            volume_info = body["items"][0]["volumeInfo"]
        except (KeyError, IndexError, TypeError) as exc:
            raise IsbnLookupError(
                f"Unexpected response structure from Google Books API for ISBN {isbn}."
            ) from exc

        return volume_info
