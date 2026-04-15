#!/usr/bin/env python3
"""
Script to populate the database with EV4 sample data.

Run:
  python3 src/scripts/load_ev4_data.py --env local
  python3 src/scripts/load_ev4_data.py --env prod
"""

import csv
import requests
import argparse
import sys
import os
import re

ENV_URLS = {
    "local": "http://localhost:8000",
    "prod": "https://vcm-51887.vm.duke.edu"
}
USERNAME = "admin"
PASSWORD = "458group2"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
AUTHORS_CSV = os.path.join(PROJECT_ROOT, "data/ev4-sample-data/authors.csv")
# BOOKS_CSV = os.path.join(PROJECT_ROOT, "data/ev4-sample-data/books.csv")
# For Backerkit testing:
BOOKS_CSV = os.path.join(PROJECT_ROOT, "data/ev4-sample-data/backerkit_testing_books.csv")
RECORDS_CSV = os.path.join(PROJECT_ROOT, "data/ev4-sample-data/records.csv")
COVERS_DIR = os.path.join(PROJECT_ROOT, "data/ev4-sample-data/img")


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


def parse_month_year(date_str):
    """Convert YYYY/MM (e.g. '2014/07') -> YYYY-MM."""
    s = (date_str or "").strip()
    if not s:
        return ""
    parts = s.split("/")
    if len(parts) == 2:
        return f"{parts[0]}-{parts[1]}"
    return s


def ensure_authors(session, base_url, authors_csv_path):
    """
    Create authors from authors.csv, including paypal/venmo fields.
    Returns a name->author dict.
    """
    print("\nImporting authors...")

    resp = session.get(f"{base_url}/api/authors/")
    if resp.status_code != 200:
        print(f"Failed to fetch authors: {resp.text}")
        sys.exit(1)

    data = resp.json()
    existing = data.get("results", data) if isinstance(data, dict) else data
    author_map = {norm_name(a["name"]): a for a in existing}

    with open(authors_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("name", "").strip()
            if not name:
                continue

            key = norm_name(name)
            if key in author_map:
                print(f"✓ Skipped: {name} (already exists)")
                continue

            payload = {
                "name": name,
                "email": row.get("email", "").strip() or email_for_author(name),
            }
            paypal = row.get("paypal_name", "").strip()
            venmo = row.get("venmo_name", "").strip()
            if paypal:
                payload["paypal"] = paypal
            if venmo:
                payload["venmo"] = venmo

            create_resp = session.post(f"{base_url}/api/authors/", json=payload)
            if create_resp.status_code == 201:
                author_obj = create_resp.json()
                author_map[key] = author_obj
                print(f"✓ Created: {name}")
            else:
                print(f"✗ Failed to create author {name}: {create_resp.text}")

    return author_map


def upload_cover_image(session, base_url, book_id, filename):
    file_path = os.path.join(COVERS_DIR, filename)
    if not os.path.exists(file_path):
        print(f"  ⚠ Image not found: {file_path}")
        return False

    with open(file_path, "rb") as f:
        files = {"file": (filename, f)}
        resp = session.post(f"{base_url}/api/books/upload-cover/", files=files)
        if resp.status_code == 201:
            cover_path = resp.json().get("cover_image_path")
            patch_resp = session.patch(f"{base_url}/api/books/{book_id}/", json={"cover_image_path": cover_path})
            if patch_resp.status_code == 200:
                print(f"  ✓ Uploaded cover: {filename}")
                return True
            else:
                print(f"  ✗ Failed to associate cover {filename}: {patch_resp.text}")
                return False
        else:
            print(f"  ✗ Failed to upload cover {filename}: {resp.text}")
            return False


def import_books(session, base_url, books_csv_path, author_map):
    print("\nImporting books...")

    success_count = 0

    with open(books_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            author_name = row.get("author", "").strip()
            author_obj = author_map.get(norm_name(author_name))
            if not author_obj:
                print(f"✗ Failed: {row.get('title')} - unknown author '{author_name}'")
                continue

            series_name = row.get("series_name", "").strip() or None
            series_position = row.get("series_index", "").strip() or None
            isbn10 = row.get("isbn10", "").strip() or None
            asin = row.get("asin", "").strip() or None
            ks_ebook = row.get("kickstarter_ebook", "").strip() or None
            ks_print = row.get("kickstarter_paperback", "").strip() or None
            released = row.get("is_released", "n").strip().lower() == "y"
            cover_image = row.get("cover_image", "").strip()

            payload = {
                "title": row["title"],
                "publication_date": parse_month_year(row.get("publish_date", "")),
                "isbn_13": row.get("isbn13", "").strip(),
                "isbn_10": isbn10,
                "amazon_asin_ebook": asin,
                "author_id": author_obj["id"],
                "series_name": series_name,
                "series_position": series_position,
                "distributor_author_royalty_rate": float(row.get("royalty_percent_distribution", 0)) / 100,
                "hand_sold_author_royalty_rate": float(row.get("royalty_percent_handsold", 0)) / 100,
                "cover_price": row.get("cover_price", "0.00"),
                "print_cost": row.get("print_cost", "0.00"),
                "kickstarter_item_tag_ebook": ks_ebook,
                "kickstarter_item_tag_print": ks_print,
                "released": released,
            }

            resp = session.post(f"{base_url}/api/books/", json=payload)

            if resp.status_code == 201:
                success_count += 1
                book_obj = resp.json()
                print(f"✓ Created: {row['title']}")
                if cover_image:
                    upload_cover_image(session, base_url, book_obj["id"], cover_image)
            elif resp.status_code == 400 and (
                "unique" in resp.text.lower() or "already exists" in resp.text.lower()
            ):
                print(f"✓ Skipped: {row['title']} (already exists)")
            else:
                print(f"✗ Failed: {row['title']} - {resp.text}")

    print(f"Created {success_count} books.")
    return success_count


def import_sales(session, base_url, records_csv_path):
    print("\nImporting sales...")

    resp = session.get(f"{base_url}/api/books/?all=true")
    if resp.status_code != 200:
        print(f"Failed to fetch books: {resp.text}")
        return 0

    data = resp.json()
    results = data.get("results", data) if isinstance(data, dict) else data
    isbn_to_book = {str(b["isbn_13"]): b for b in results if b.get("isbn_13")}

    success_count = 0

    with open(records_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            isbn13 = (row.get("isbn13") or "").strip()
            if not isbn13 or isbn13 not in isbn_to_book:
                print(f"⚠ Skipping sale for unknown ISBN: {isbn13}")
                continue

            book = isbn_to_book[isbn13]
            sale_date = parse_month_year(row.get("record_date", ""))
            source = row.get("source", "distributor").strip().lower()
            distributor = row.get("distributor", "").strip()
            format_val = row.get("format", "print").strip()
            currency = row.get("iso_currency", "USD").strip()
            revenue = row.get("publisher_revenue", "").strip()
            author_paid = (row.get("author_paid", "n") or "n").strip().lower() == "y"

            qty_raw = row.get("qty_sold", "").strip()
            quantity = int(qty_raw) if qty_raw else None

            kenp_raw = row.get("kenp", "").strip()
            kenp = int(kenp_raw) if kenp_raw else None

            sale_data = {
                "book": book["id"],
                "date": sale_date,
                "sale_source": source,
                "format": format_val,
                "author_paid": author_paid,
            }

            if quantity is not None:
                sale_data["quantity"] = quantity
            if kenp is not None:
                sale_data["kenp"] = kenp

            if source == "distributor":
                if distributor:
                    sale_data["distributor"] = distributor
                if revenue:
                    sale_data["publisher_revenue_original"] = revenue
                if currency:
                    sale_data["currency"] = currency
            elif source in ("handsold", "kickstarter"):
                sale_data["currency"] = "USD"
                # Revenue is computed by the backend from cover_price - print_cost

            resp = session.post(f"{base_url}/api/sales/", json=sale_data)

            if resp.status_code == 201:
                success_count += 1
            else:
                print(f"✗ Failed sale for {isbn13} on {sale_date}: {resp.text}")

    print(f"Created {success_count} sales records.")
    return success_count


def main():
    parser = argparse.ArgumentParser(description="Populate the database with EV4 sample data.")
    parser.add_argument("--env", choices=["local", "prod"], default="local", help="Environment to populate")
    parser.add_argument("--url", help="Override base URL directly")
    parser.add_argument("--username", default=USERNAME)
    parser.add_argument("--password", default=PASSWORD)
    parser.add_argument("--skip-authors", action="store_true")
    parser.add_argument("--skip-books", action="store_true")
    parser.add_argument("--skip-sales", action="store_true")
    args = parser.parse_args()

    base_url = args.url if args.url else ENV_URLS[args.env]
    session = get_session(base_url, args.username, args.password)

    author_map = {}
    if not args.skip_authors:
        author_map = ensure_authors(session, base_url, AUTHORS_CSV)
    else:
        # Still need the map for book creation
        resp = session.get(f"{base_url}/api/authors/")
        data = resp.json()
        existing = data.get("results", data) if isinstance(data, dict) else data
        author_map = {norm_name(a["name"]): a for a in existing}

    if not args.skip_books:
        import_books(session, base_url, BOOKS_CSV, author_map)

    if not args.skip_sales:
        import_sales(session, base_url, RECORDS_CSV)

    print("\nDone.")


if __name__ == "__main__":
    main()
