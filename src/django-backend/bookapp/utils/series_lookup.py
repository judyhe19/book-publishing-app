"""
Series lookup utility using the Open Library Search API.

Fetches series name and position for a book by ISBN. Series data is
community-contributed and best-effort — all failures are logged and return
null values rather than raising exceptions.

Usage:
    from bookapp.utils.series_lookup import SeriesLookup

    result = SeriesLookup().fetch("9780439708180")
    # {"series_name": "Harry Potter", "series_position": 1}
    # or {"series_name": None, "series_position": None} if not found
"""

import logging
import re

import requests


logger = logging.getLogger(__name__)

OPEN_LIBRARY_SEARCH_URL = "https://openlibrary.org/search.json"

_EMPTY = {"series_name": None, "series_position": None}


class SeriesLookup:
    """
    Fetches series metadata from the Open Library Search API by ISBN.

    No API key required. All network and parse failures are logged as warnings
    and return empty results — series data is supplementary and non-blocking.
    """

    def fetch(self, isbn: str) -> dict:
        """
        Look up series information for a book by ISBN.

        Args:
            isbn: ISBN-10 or ISBN-13 string (hyphens/spaces are stripped).

        Returns:
            {"series_name": str | None, "series_position": int | None}
        """
        isbn = isbn.replace("-", "").replace(" ", "").strip()

        response = self._fetch_raw(isbn)
        if response is None:
            return _EMPTY

        result = self._parse(response, isbn)
        if result["series_name"] is None:
            logger.warning("Open Library returned no series data for ISBN %s", isbn)
        else:
            logger.warning(
                "Open Library series for ISBN %s: name=%r, position=%s",
                isbn, result["series_name"], result["series_position"],
            )
        return result

    # ──────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────

    def _fetch_raw(self, isbn: str) -> requests.Response | None:
        """Fetch from Open Library. Returns None on any failure."""
        try:
            response = requests.get(
                OPEN_LIBRARY_SEARCH_URL,
                params={"isbn": isbn, "fields": "series"},
                timeout=10,
            )
        except requests.RequestException as exc:
            logger.warning("Open Library network error for ISBN %s: %s", isbn, exc)
            return None

        if not response.ok:
            logger.warning(
                "Open Library returned HTTP %s for ISBN %s",
                response.status_code, isbn,
            )
            return None

        return response

    def _parse(self, response: requests.Response, isbn: str) -> dict:
        """Extract series name and position from the Open Library response."""
        try:
            body = response.json()
        except ValueError:
            logger.warning("Open Library returned invalid JSON for ISBN %s", isbn)
            return _EMPTY

        docs = body.get("docs") or []
        if not docs:
            logger.warning("Open Library returned no results for ISBN %s", isbn)
            return _EMPTY

        # The series field is a list of strings on the first matching doc.
        series_list = docs[0].get("series") or []
        if not series_list:
            return _EMPTY

        series_name, series_position = _parse_series_string(series_list[0])
        return {"series_name": series_name, "series_position": series_position}


# ──────────────────────────────────────────────────────────────────────────────
# Parsing helpers (module-level — no class state needed)
# ──────────────────────────────────────────────────────────────────────────────

def _parse_series_string(raw: str) -> tuple[str | None, int | None]:
    """
    Parse a freeform Open Library series string into (name, position).

    Handles common formats:
      "Discworld #5"                → ("Discworld", 5)
      "Wheel of Time, 3"            → ("Wheel of Time", 3)
      "Harry Potter Book 1"         → ("Harry Potter", 1)
      "The Expanse Vol. 2"          → ("The Expanse", 2)
      "Some Series"                 → ("Some Series", None)
    """
    s = raw.strip()
    if not s:
        return None, None

    # Pattern 1: "Name #N" or "Name #N.5"
    m = re.match(r'^(.+?)\s*#\s*(\d+(?:\.\d+)?)$', s)
    if m:
        return m.group(1).strip(), _parse_position(m.group(2))

    # Pattern 2: "Name, N" at end
    m = re.match(r'^(.+?),\s*(\d+(?:\.\d+)?)$', s)
    if m:
        return m.group(1).strip(), _parse_position(m.group(2))

    # Pattern 3: "Name Book/Vol/Volume/Part N"
    m = re.match(
        r'^(.+?)\s+(?:Book|Vol\.?|Volume|Part)\s*(\d+(?:\.\d+)?)\s*$',
        s,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).strip(), _parse_position(m.group(2))

    # No position found — return full string as series name
    return s, None


def _parse_position(raw: str) -> int | None:
    """
    Convert a position string to an integer.

    "1" → 1, "1.0" → 1, "1.5" → None (fractional positions like novellas
    can't map to integer series positions in this system).
    """
    try:
        val = float(raw)
        if val == int(val) and val >= 1:
            return int(val)
        return None
    except (ValueError, TypeError):
        return None
