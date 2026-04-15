# Feature Guide: ISBN Lookup (Extra Credit)

## Overview

The ISBN Lookup feature allows users to pre-fill the Create Book form by entering an ISBN. When triggered, the backend queries the Google Books API, normalizes the returned metadata, and attempts to automatically match the book's author against existing database records. The user can review and adjust any pre-filled fields before submitting.

This eliminates manual data entry for title, publication date, ISBN fields, and cover image when adding a book that already exists in the Google Books catalog.

---

## Design

### Backend

**`bookapp/utils/isbn_lookup.py` — `IsbnLookup`**

Queries the Google Books API at `https://www.googleapis.com/books/v1/volumes` using the `isbn:<value>` search parameter. Accepts ISBN-10 or ISBN-13 (hyphens and spaces are stripped). Uses the `GOOGLE_BOOKS_API_KEY` environment variable if present. Raises `IsbnLookupError` for network failures, non-2xx responses, or empty results.

**`bookapp/utils/isbn_normalizer.py` — `normalize_volume_info`**

Transforms the raw `volumeInfo` dict from Google Books into the fields the Create Book form expects:
- `title`
- `isbn_13`, `isbn_10`
- `publication_date` — normalized to `YYYY-MM` from Google's inconsistent formats (`"2018"`, `"2018-01"`, `"2018-01-15"`)
- `cover_image_url` — best available resolution from `imageLinks`
- `authors` — raw name strings as returned by Google

**`bookapp/utils/author_matcher.py` — `match_author`**

Fuzzy-matches the first author name from Google Books against all `Author` records in the database. Matching works in two stages:
1. Token normalization (lowercase, strip punctuation, sort tokens) — handles `"Huxley, Aldous"` matching `"Aldous Huxley"` without any scoring.
2. `rapidfuzz.token_sort_ratio` for fuzzy similarity — catches abbreviations, middle names, and minor typos.

A match is returned only if the score meets the `FUZZY_MATCH_THRESHOLD` of 80. The result includes `author_id`, `name`, `confidence` (0–100), and `match_type` (`"exact"` or `"fuzzy"`).

**`bookapp/views/isbn_lookup.py` — `IsbnLookupView`**

`GET /api/books/isbn-lookup/?isbn=<isbn>` — orchestrates the lookup, normalization, and author matching, returning a single JSON response to the frontend.

**`bookapp/views/isbn_cover_proxy.py`**

`GET /api/books/isbn-lookup/cover/?url=<url>` — proxies Google Books cover images through the backend to avoid browser CORS restrictions during the preview step. Does not store the image.

**`bookapp/views/cover_download.py`**

`POST /api/books/download-cover/` — downloads a Google Books cover image and saves it to `static/img/covers/` at submit time (not during preview). Returns a `cover_image_path` suitable for storing in the database.

### Frontend

**`isbnApi.js`**

Three functions:
- `lookupIsbn(isbn)` — calls the lookup endpoint
- `proxyCoverUrl(url)` — builds the proxy URL for `<img src>` display
- `downloadCoverFromUrl(url)` — called at submit time to persist the cover

**`IsbnLookupModal.jsx`**

A modal dialog with a single ISBN input field. On submit it calls `lookupIsbn`, then passes the result to an `onSuccess` callback and closes. Handles loading state and error display inline.

**`CreateBookPage.jsx`**

An "Import from ISBN" button in the page header opens the modal. On success (`onIsbnSuccess`):
- Title, ISBN-13, ISBN-10, and publication month are pre-filled
- The cover image URL is stored temporarily; the image is only downloaded when the form is submitted
- If `author_match` is returned, the author picker is pre-selected automatically
- If Google Books returned an author name but no database match was found, a warning banner is shown prompting the user to select an author manually

At submit time, cover image resolution priority is: manual file upload > ISBN cover URL > existing path.

---

## Benefits

- **Speed** — adding a published book takes seconds instead of manually copying metadata fields
- **Accuracy** — ISBNs uniquely identify books, so title, date, and ISBN fields are reliably correct
- **Author matching** — fuzzy matching handles name formatting differences common between external data sources and internal records
- **Non-destructive** — the lookup only pre-fills; users can edit or override any field before saving

---

## Demonstration Walkthrough

**Prerequisites:** The app must be running and at least one author must exist in the database whose name matches a book in the Google Books catalog.

1. Navigate to **Books → Create Book**.
2. Click the **"Import from ISBN"** button in the top-right corner of the form.
3. In the modal, enter an ISBN-13 or ISBN-10. For example:
   - `9780060850524` — *Brave New World* by Aldous Huxley
   - `9780441172719` — *Dune* by Frank Herbert
4. Click **Look Up**.
5. The modal closes and the form is pre-filled with:
   - Title
   - ISBN-13 and ISBN-10
   - Publication month and year
   - Author (if a match was found in the database)
   - Cover image preview (if Google Books has one)
6. If the author was not automatically matched, a warning banner appears. Select the correct author from the author picker manually.
7. Fill in any remaining required fields (cover price, print cost, royalty rates) that cannot be sourced from Google Books.
8. Click **Create**. The cover image is downloaded from Google Books and stored at this point.
