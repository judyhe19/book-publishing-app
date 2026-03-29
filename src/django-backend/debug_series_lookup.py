"""
Standalone debug script for Open Library series lookup.

Run from the django-backend directory:
    python debug_series_lookup.py

No Django setup required — hits the Open Library API directly and
prints everything returned so you can see exactly what the API gives us.
"""

import json
import requests

OPEN_LIBRARY_SEARCH_URL = "https://openlibrary.org/search.json"

TEST_ISBNS = [
    ("Harry Potter and the Philosopher's Stone", "9780747532699"),
    ("The Fellowship of the Ring", "9780547928210"),
]


def fetch_raw(isbn: str) -> dict | None:
    """Make the exact same request SeriesLookup makes, return parsed JSON."""
    url = OPEN_LIBRARY_SEARCH_URL
    params = {"isbn": isbn, "fields": "series"}
    print(f"  GET {url}")
    print(f"  params: {params}")

    try:
        response = requests.get(url, params=params, timeout=10)
    except requests.RequestException as exc:
        print(f"  NETWORK ERROR: {exc}")
        return None

    print(f"  HTTP status: {response.status_code}")
    print(f"  URL called:  {response.url}")

    if not response.ok:
        print(f"  ERROR response body: {response.text[:500]}")
        return None

    try:
        return response.json()
    except ValueError:
        print(f"  INVALID JSON: {response.text[:500]}")
        return None


def fetch_without_fields_filter(isbn: str) -> dict | None:
    """Same request but without the fields filter — see what Open Library returns in full."""
    url = OPEN_LIBRARY_SEARCH_URL
    params = {"isbn": isbn}
    print(f"  GET {url}")
    print(f"  params: {params}")

    try:
        response = requests.get(url, params=params, timeout=10)
    except requests.RequestException as exc:
        print(f"  NETWORK ERROR: {exc}")
        return None

    print(f"  HTTP status: {response.status_code}")

    if not response.ok:
        return None

    try:
        return response.json()
    except ValueError:
        return None


def main():
    for title, raw_isbn in TEST_ISBNS:
        isbn = raw_isbn.replace("-", "").replace(" ", "").strip()
        print("=" * 70)
        print(f"BOOK:  {title}")
        print(f"ISBN:  {raw_isbn}  →  stripped: {isbn}")
        print()

        # ── Test 1: exact request SeriesLookup makes ──────────────────────
        print("── Request 1: with fields=series (what SeriesLookup sends) ──")
        body = fetch_raw(isbn)
        if body is not None:
            print(f"  numFound:  {body.get('numFound')}")
            docs = body.get("docs") or []
            print(f"  docs count: {len(docs)}")
            if docs:
                print(f"  docs[0] keys: {list(docs[0].keys())}")
                series = docs[0].get("series")
                print(f"  docs[0]['series']: {series!r}")
            else:
                print("  docs is empty — no results for this ISBN")
        print()

        # ── Test 2: full response (no fields filter) ──────────────────────
        print("── Request 2: without fields filter (full doc) ──")
        body2 = fetch_without_fields_filter(isbn)
        if body2 is not None:
            docs2 = body2.get("docs") or []
            print(f"  numFound:  {body2.get('numFound')}")
            print(f"  docs count: {len(docs2)}")
            if docs2:
                doc = docs2[0]
                print(f"  title:    {doc.get('title')!r}")
                print(f"  series:   {doc.get('series')!r}")
                # Print all keys so we can see what fields are available
                print(f"  all keys: {sorted(doc.keys())}")
        print()

    print("=" * 70)
    print("Done.")


if __name__ == "__main__":
    main()
