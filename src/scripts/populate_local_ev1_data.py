#!/usr/bin/env python3
"""
Script to populate the LOCAL database with EV1 review data from CSV files.

Run:
  python src/scripts/populate_local_ev1_data.py
"""

import csv
import requests
import argparse
import sys
import os
import re

BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "458group2"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
BOOKS_CSV = os.path.join(PROJECT_ROOT, "data/ev1-review-data/books.csv")
RECORDS_CSV = os.path.join(PROJECT_ROOT, "data/ev1-review-data/records.csv")

DEFAULT_COVER_PRICE = "19.99"
DEFAULT_PRINT_COST = "5.00"


def norm_name(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


def email_for_author(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "", norm_name(name))
    if not slug:
        slug = "author"
    return f"{slug}@example.com"


def get_session(base_url, username, password):
    s = requests.Session()

    try:
        csrf_resp = s.get(f"{base_url}/api/csrf")
        csrf_resp.raise_for_status()
        if "csrftoken" in s.cookies:
            s.headers.update({"X-CSRFToken": s.cookies["csrftoken"]})
    except Exception:
        pass

    print(f"Logging in as {username} to {base_url}...")
    resp = s.post(
        f"{base_url}/api/user/login",
        json={"username": username, "password": password},
    )

    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code} {resp.text}")
        sys.exit(1)

    if "csrftoken" in s.cookies:
        s.headers.update({"X-CSRFToken": s.cookies["csrftoken"]})

    print("Login successful.")
    return s


def parse_date(date_str):
    """
    Convert MM/YYYY -> YYYY-MM
    """
    s = (date_str or "").strip()
    if "/" in s:
        month, year = s.split("/")
        return f"{year}-{month.zfill(2)}"
    return s


def ensure_authors(session, base_url, author_names):
    print("Fetching existing authors...")
    resp = session.get(f"{base_url}/api/authors/?all=true")

    if resp.status_code != 200:
        print(resp.text)
        sys.exit(1)

    data = resp.json()
    existing_authors = data.get("results", data) if isinstance(data, dict) else data
    author_map = {norm_name(a["name"]): a for a in existing_authors}

    for name in author_names:
        key = norm_name(name)
        if key not in author_map:
            new_author = {"name": name, "email": email_for_author(name)}
            create_resp = session.post(f"{base_url}/api/authors/", json=new_author)
            if create_resp.status_code == 201:
                author_map[key] = create_resp.json()
            else:
                print(f"Failed to create author {name}: {create_resp.text}")

    return author_map


def import_books(session, base_url, books_csv_path, cover_price, print_cost):
    print("\nImporting books...")
    books_data = []
    all_authors = set()

    with open(books_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            authors = [a.strip() for a in row.get("author", "").split(",") if a.strip()]
            for a in authors:
                all_authors.add(a)

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

    author_map = ensure_authors(session, base_url, all_authors)

    success_count = 0

    for book in books_data:
        if not book["authors"]:
            print(f"✗ Failed: {book['title']} - no authors in CSV row")
            continue

        primary_author_name = book["authors"][0]
        author_obj = author_map.get(norm_name(primary_author_name))
        if not author_obj:
            print(f"✗ Failed: {book['title']} - could not map author '{primary_author_name}'")
            continue

        payload = {
            "title": book["title"],
            "publication_date": book["publication_date"],
            "isbn_13": book["isbn13"],
            "isbn_10": book["isbn10"] if book["isbn10"] else None,
            "author_id": author_obj["id"],
            "cover_price": str(cover_price),
            "print_cost": str(print_cost),
            "royalty_rate": book["royalty_percent"],
        }

        resp = session.post(f"{base_url}/api/books/", json=payload)

        if resp.status_code == 201:
            success_count += 1
            print(f"✓ Created: {book['title']}")
        else:
            print(f"✗ Failed: {book['title']} - {resp.text}")

    print(f"Created {success_count} books.")
    return success_count


def _book_royalty_rate(book_obj) -> float:
    for k in ("royalty_rate", "author_royalty_rate", "royalty_percent"):
        if k in book_obj and book_obj[k] is not None:
            try:
                return float(book_obj[k])
            except Exception:
                pass
    return 0.1


def import_sales(session, base_url, records_csv_path):
    print("\nImporting sales...")

    resp = session.get(f"{base_url}/api/books/?all=true")
    if resp.status_code != 200:
        print(resp.text)
        return 0

    data = resp.json()
    books = data.get("results", data) if isinstance(data, dict) else data

    isbn_to_book = {b["isbn_13"]: b for b in books if b.get("isbn_13")}

    sales_data = []

    with open(records_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            isbn13 = row.get("isbn13")
            if isbn13 not in isbn_to_book:
                continue

            book = isbn_to_book[isbn13]

            sale_date = parse_date(row.get("record_date", ""))
            quantity = int(row.get("units_sold", 0))
            revenue = float(row.get("total_revenue", 0))
            royalty_paid = (row.get("royalty_paid", "n") or "n").lower() == "y"

            rate = _book_royalty_rate(book)
            total_author_royalty = revenue * rate

            sales_data.append(
                {
                    "book": book["id"],
                    "date": sale_date,
                    "quantity": quantity,
                    "publisher_revenue": str(revenue),
                    "sale_source": "distributor",
                    "author_royalty": str(round(total_author_royalty, 2)),
                    "author_paid": royalty_paid,
                }
            )

    if not sales_data:
        print("No sales to import.")
        return 0

    print(f"Creating {len(sales_data)} sales records...")
    resp = session.post(f"{base_url}/api/sales/create-many/", json=sales_data)

    if resp.status_code == 201:
        print("✓ Sales imported successfully.")
        return len(sales_data)

    print("Failed:", resp.text)
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=BASE_URL)
    parser.add_argument("--username", default=USERNAME)
    parser.add_argument("--password", default=PASSWORD)
    parser.add_argument("--skip-books", action="store_true")
    parser.add_argument("--skip-sales", action="store_true")
    parser.add_argument("--cover-price", default=DEFAULT_COVER_PRICE)
    parser.add_argument("--print-cost", default=DEFAULT_PRINT_COST)
    args = parser.parse_args()

    session = get_session(args.url, args.username, args.password)

    if not args.skip_books:
        import_books(
            session,
            args.url,
            BOOKS_CSV,
            str(args.cover_price),
            str(args.print_cost),
        )

    if not args.skip_sales:
        import_sales(session, args.url, RECORDS_CSV)


if __name__ == "__main__":
    main()