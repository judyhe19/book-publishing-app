#!/usr/bin/env python3
"""
Script to populate the LOCAL database with EV1 review data from CSV files.

Usage:
    python src/scripts/populate_local_ev1_data.py

Configure BASE_URL, USERNAME, and PASSWORD below if needed.

Default: Connect to local server (http://localhost:8000)
    python src/scripts/populate_local_ev1_data.py

Custom options:
    python src/scripts/populate_local_ev1_data.py --url http://127.0.0.1:8000
    python src/scripts/populate_local_ev1_data.py --skip-books  # Only import sales
    python src/scripts/populate_local_ev1_data.py --skip-sales  # Only import books
"""
import csv
import requests
import argparse
import sys
import os
import re

# Configuration - Update these to match your local server
BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "458group2"  # Default password for local dev

# CSV file paths (relative to project root)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
BOOKS_CSV = os.path.join(PROJECT_ROOT, "data/ev1-review-data/books.csv")
RECORDS_CSV = os.path.join(PROJECT_ROOT, "data/ev1-review-data/records.csv")


# -----------------------------
# Helpers
# -----------------------------
def norm_name(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


def email_for_author(name: str) -> str:
    """
    Deterministic (but unique-enough) placeholder email for local data.
    Example: "J. R. R. Tolkien" -> "jrrtolkien@example.com"
    """
    slug = re.sub(r"[^a-z0-9]+", "", norm_name(name))
    if not slug:
        slug = "author"
    return f"{slug}@example.com"


def get_session(base_url, username, password):
    """
    Log in and return a session with the auth cookie/token.
    """
    s = requests.Session()

    # 1. Get CSRF token
    try:
        csrf_resp = s.get(f"{base_url}/api/csrf")
        csrf_resp.raise_for_status()
        if "csrftoken" in s.cookies:
            s.headers.update({"X-CSRFToken": s.cookies["csrftoken"]})
    except Exception as e:
        print(f"Warning: Could not fetch CSRF token: {e}")

    # 2. Login
    login_url = f"{base_url}/api/user/login"
    payload = {"username": username, "password": password}

    print(f"Logging in as {username} to {base_url}...")
    try:
        resp = s.post(login_url, json=payload)
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to {base_url}. Is the server running?")
        sys.exit(1)

    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code} {resp.text}")
        sys.exit(1)

    print("Login successful.")
    if "csrftoken" in s.cookies:
        s.headers.update({"X-CSRFToken": s.cookies["csrftoken"]})

    return s


def parse_date(date_str):
    """
    Parse date string in MM/YYYY format and return YYYY-MM-DD format.
    Defaults to first day of month.
    """
    try:
        if "/" in date_str and len(date_str.split("/")) == 2:
            month, year = date_str.split("/")
            return f"{year}-{month.zfill(2)}-01"
        return date_str
    except Exception as e:
        print(f"Warning: Could not parse date '{date_str}': {e}")
        return date_str


def ensure_authors(session, base_url, author_names):
    """
    Ensure authors exist in the database and return a mapping of name -> author object.
    Creates authors if they don't exist.

    IMPORTANT: Author now requires `email`, so we include it when creating.
    """
    print("Fetching existing authors...")
    try:
        resp = session.get(f"{base_url}/api/authors/?all=true")
    except Exception:
        resp = session.get(f"{base_url}/api/authors/")

    if resp.status_code != 200:
        print(f"Failed to fetch authors: {resp.status_code}")
        print(resp.text[:300])
        sys.exit(1)

    data = resp.json()
    existing_authors = data.get("results", data) if isinstance(data, dict) else data

    # Create name -> author mapping (case-insensitive + normalized)
    author_map = {norm_name(a["name"]): a for a in existing_authors}

    # Find authors that need to be created
    for name in author_names:
        key = norm_name(name)
        if not key:
            continue

        if key not in author_map:
            print(f"  Creating author: {name}")
            new_author = {
                "name": name,
                "email": email_for_author(name),  # ✅ ADDED
            }

            create_resp = session.post(f"{base_url}/api/authors/", json=new_author)

            if create_resp.status_code == 201:
                author_obj = create_resp.json()
                author_map[key] = author_obj
            else:
                # If email collided (unique constraint), retry with a deterministic suffix
                if create_resp.status_code == 400 and "email" in create_resp.text.lower():
                    retry_author = {
                        "name": name,
                        "email": email_for_author(f"{name}-{abs(hash(name)) % 100000}"),
                    }
                    create_resp2 = session.post(f"{base_url}/api/authors/", json=retry_author)
                    if create_resp2.status_code == 201:
                        author_obj = create_resp2.json()
                        author_map[key] = author_obj
                        continue

                print(f"  Failed to create author '{name}': {create_resp.status_code} {create_resp.text[:300]}")

    return author_map


def import_books(session, base_url, books_csv_path):
    """
    Import books from CSV file.
    """
    print(f"\n{'='*50}")
    print(f"Importing books from {books_csv_path}")
    print(f"{'='*50}")

    books_data = []
    all_authors = set()

    with open(books_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("title"):
                continue

            author_str = row.get("author", "")
            authors = [a.strip() for a in author_str.split(",") if a.strip()]

            for author in authors:
                all_authors.add(author)

            books_data.append(
                {
                    "title": row["title"],
                    "authors": authors,
                    "isbn13": row.get("isbn13", ""),
                    "isbn10": row.get("isbn10", ""),
                    "publication_date": parse_date(row.get("publication_date", "")),
                    "royalty_percent": float(row.get("royalty_percent", 0.1)),
                }
            )

    print(f"Found {len(books_data)} books and {len(all_authors)} unique authors in CSV.")

    author_map = ensure_authors(session, base_url, all_authors)

    success_count = 0
    url = f"{base_url}/api/books/"

    for book in books_data:
        authors_payload = []

        for author_name in book["authors"]:
            key = norm_name(author_name)
            if key in author_map:
                authors_payload.append(
                    {
                        "author_name": author_name,
                        "royalty_rate": book["royalty_percent"],
                    }
                )

        payload = {
            "title": book["title"],
            "publication_date": book["publication_date"],
            "isbn_13": book["isbn13"],
            "isbn_10": book["isbn10"] if book["isbn10"] else None,
            "authors": authors_payload,
        }

        resp = session.post(url, json=payload)

        if resp.status_code == 201:
            success_count += 1
            print(f"  ✓ Created: {book['title']}")
        else:
            print(f"  ✗ Failed: {book['title']} - {resp.status_code}: {resp.text[:200]}")

    print(f"\n✓ Successfully created {success_count}/{len(books_data)} books.")
    return success_count


def import_sales(session, base_url, records_csv_path):
    """
    Import sales records from CSV file.
    """
    print(f"\n{'='*50}")
    print(f"Importing sales from {records_csv_path}")
    print(f"{'='*50}")

    print("Fetching books...")
    try:
        resp = session.get(f"{base_url}/api/books/?all=true")
    except Exception:
        resp = session.get(f"{base_url}/api/books/")

    if resp.status_code != 200:
        print(f"Failed to fetch books: {resp.status_code}")
        print(resp.text[:300])
        return 0

    data = resp.json()
    books = data.get("results", data) if isinstance(data, dict) else data

    isbn_to_book = {}
    for book in books:
        if book.get("isbn_13"):
            isbn_to_book[book["isbn_13"]] = book

    print(f"Found {len(books)} books in database.")

    sales_data = []
    skipped = 0

    with open(records_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            isbn13 = row.get("isbn13", "")
            if not isbn13:
                continue

            if isbn13 not in isbn_to_book:
                print(f"  ⚠ Book not found for ISBN-13: {isbn13}")
                skipped += 1
                continue

            book = isbn_to_book[isbn13]

            sale_date = parse_date(row.get("record_date", ""))
            quantity = int(row.get("units_sold", 0))
            revenue = float(row.get("total_revenue", 0))
            royalty_paid = row.get("royalty_paid", "n").lower() == "y"

            author_paid_map = {}
            if "authors" in book:
                for ab in book["authors"]:
                    author_paid_map[str(ab["author_id"])] = royalty_paid

            sales_data.append(
                {
                    "book": book["id"],
                    "date": sale_date,
                    "quantity": quantity,
                    "publisher_revenue": str(revenue),
                    "author_paid": author_paid_map,
                }
            )

    if skipped > 0:
        print(f"⚠ Skipped {skipped} sales records due to missing books.")

    if not sales_data:
        print("No sales records to import.")
        return 0

    print(f"Importing {len(sales_data)} sales records...")

    url = f"{base_url}/api/sales/create-many/"
    resp = session.post(url, json=sales_data)

    if resp.status_code == 201:
        print(f"\n✓ Successfully created {len(sales_data)} sales records.")
        total_revenue = sum(float(s["publisher_revenue"]) for s in sales_data)
        total_units = sum(s["quantity"] for s in sales_data)
        print(f"  Total revenue: ${total_revenue:,.2f}")
        print(f"  Total units sold: {total_units:,}")
        return len(sales_data)
    else:
        print(f"Failed to create sales: {resp.status_code} {resp.text}")
        return 0


def main():
    parser = argparse.ArgumentParser(description="Import EV1 review data (books and sales) from CSV files (LOCAL VERSION).")
    parser.add_argument("--url", default=BASE_URL, help=f"Base URL of the server (default: {BASE_URL})")
    parser.add_argument("--username", default=USERNAME, help=f"Login username (default: {USERNAME})")
    parser.add_argument("--password", default=PASSWORD, help=f"Login password (default: {PASSWORD})")
    parser.add_argument("--books-csv", default=BOOKS_CSV, help=f"Path to books CSV file")
    parser.add_argument("--records-csv", default=RECORDS_CSV, help=f"Path to sales records CSV file")
    parser.add_argument("--skip-books", action="store_true", help="Skip book import")
    parser.add_argument("--skip-sales", action="store_true", help="Skip sales import")

    args = parser.parse_args()

    print(f"\n{'#'*60}")
    print("# EV1 Review Data Import Script (LOCAL)")
    print(f"# Target: {args.url}")
    print(f"# Books CSV: {args.books_csv}")
    print(f"# Records CSV: {args.records_csv}")
    print(f"{'#'*60}\n")

    if not args.skip_books and not os.path.exists(args.books_csv):
        print(f"Error: Books CSV file not found: {args.books_csv}")
        sys.exit(1)
    if not args.skip_sales and not os.path.exists(args.records_csv):
        print(f"Error: Records CSV file not found: {args.records_csv}")
        sys.exit(1)

    try:
        session = get_session(args.url, args.username, args.password)

        books_created = 0
        sales_created = 0

        if not args.skip_books:
            books_created = import_books(session, args.url, args.books_csv)
        else:
            print("Skipping book import.")

        if not args.skip_sales:
            sales_created = import_sales(session, args.url, args.records_csv)
        else:
            print("Skipping sales import.")

        print(f"\n{'#'*60}")
        print("# Import complete!")
        print(f"# Books created: {books_created}")
        print(f"# Sales created: {sales_created}")
        print(f"{'#'*60}\n")

    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to {args.url}. Is the server running?")
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()