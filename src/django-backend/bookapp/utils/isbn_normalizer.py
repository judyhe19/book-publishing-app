"""
Normalizes a Google Books volumeInfo dict into the fields needed for book creation.

Usage:
    from bookapp.utils.isbn_normalizer import normalize_volume_info

    normalized = normalize_volume_info(volume_info)
"""


def normalize_volume_info(volume_info: dict) -> dict:
    """
    Extract and normalize book creation fields from a Google Books volumeInfo dict.

    Author matching and series detection are handled separately.

    Returns a dict with:
        title            (str | None)
        isbn_13          (str | None)
        isbn_10          (str | None)
        publication_date (str | None)  YYYY-MM-DD, or None if unparseable
        cover_image_url  (str | None)
        authors          (list[str])   raw author name strings
    """
    return {
        "title": _extract_title(volume_info),
        "isbn_13": _extract_isbn(volume_info, "ISBN_13"),
        "isbn_10": _extract_isbn(volume_info, "ISBN_10"),
        "publication_date": _extract_publication_date(volume_info),
        "cover_image_url": _extract_cover_image_url(volume_info),
        "authors": volume_info.get("authors") or [],
    }


# ──────────────────────────────────────────────────────────────────────────────
# Private helpers
# ──────────────────────────────────────────────────────────────────────────────

def _extract_title(volume_info: dict) -> str | None:
    return volume_info.get("title") or None


def _extract_isbn(volume_info: dict, isbn_type: str) -> str | None:
    """Return the identifier value for the given type (ISBN_10 or ISBN_13)."""
    identifiers = volume_info.get("industryIdentifiers") or []
    for entry in identifiers:
        if entry.get("type") == isbn_type:
            return entry.get("identifier") or None
    return None


def _extract_publication_date(volume_info: dict) -> str | None:
    """
    Normalize publishedDate to YYYY-MM-DD.

    Google Books may return:
      "2018"        → "2018-01-01"
      "2018-01"     → "2018-01-01"
      "2018-01-15"  → "2018-01-15"
    Returns None if the field is missing or unparseable.
    """
    raw = (volume_info.get("publishedDate") or "").strip()
    if not raw:
        return None

    parts = raw.split("-")
    try:
        year = int(parts[0])
        month = int(parts[1]) if len(parts) > 1 else 1
        day = int(parts[2]) if len(parts) > 2 else 1
    except (ValueError, IndexError):
        return None

    return f"{year:04d}-{month:02d}-{day:02d}"


def _extract_cover_image_url(volume_info: dict) -> str | None:
    """Return the best available cover image URL from imageLinks."""
    image_links = volume_info.get("imageLinks") or {}
    # Prefer higher resolution when available
    for key in ("large", "medium", "small", "thumbnail", "smallThumbnail"):
        url = image_links.get(key)
        if url:
            return url
    return None
