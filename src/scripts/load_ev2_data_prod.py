#!/usr/bin/env python3
"""
Script to populate the PRODUCTION database with EV2 sample data from CSV files.

Run:
  python src/scripts/load_ev2_data_prod.py
"""

import csv
import requests
import argparse
import sys
import os
import re

BASE_URL = "https://vcm-51984.vm.duke.edu"
USERNAME = "admin"
PASSWORD = "458group2"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
BOOKS_CSV = os.path.join(PROJECT_ROOT, "data/ev2/ev2-sample-data/books.csv")
RECORDS_CSV = os.path.join(PROJECT_ROOT, "data/ev2/ev2-sample-data/sales_records.csv")
COVERS_DIR = os.path.join(PROJECT_ROOT, "data/ev2/ev2-sample-data")

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
    """
    Convert Month YYYY (e.g., 'July 2014') -> YYYY-MM
    """
    s = (date_str or "").strip()
    if not s:
        return ""
    months = {
        "January": "01", "February": "02", "March": "03", "April": "04",
        "May": "05", "June": "06", "July": "07", "August": "08",
        "September": "09", "October": "10", "November": "11", "December": "12"
    }
    parts = s.split(" ")
    if len(parts) == 2:
        month_name = parts[0]
        year = parts[1]
        for m_name, m_num in months.items():
            if m_name.lower() == month_name.lower():
                return f"{year}-{m_num}"
    return s

def ensure_authors(session, base_url, author_names):
    print("Fetching existing authors...")
    resp = session.get(f"{base_url}/api/authors/")

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

def upload_cover_image(session, base_url, book_id, filename):
    file_path = os.path.join(COVERS_DIR, filename)
    if not os.path.exists(file_path):
        print(f"  ⚠ Image not found: {file_path}")
        return False

    with open(file_path, "rb") as f:
        files = {"file": (filename, f)}
        resp = session.post(f"{base_url}/api/books/upload-cover/", files=files)
        if resp.status_code == 201:
            print(f"  ✓ Uploaded cover: {filename}")
            cover_path = resp.json().get("cover_image_path")
            
            # Now we need to patch the book to associate the new cover image
            patch_resp = session.patch(f"{base_url}/api/books/{book_id}/", json={"cover_image_path": cover_path})
            if patch_resp.status_code == 200:
                print(f"  ✓ Associated cover with book: {filename}")
                return True
            else:
                print(f"  ✗ Failed to associate cover with book {filename}: {patch_resp.text}")
                return False
        else:
            print(f"  ✗ Failed to upload cover {filename}: {resp.text}")
            return False

def import_books(session, base_url, books_csv_path):
    print("\nImporting books...")
    books_data = []
    all_authors = set()

    with open(books_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            author_raw = row.get("author", "").strip()
            authors = [a.strip() for a in author_raw.split(",") if a.strip()]
            for a in authors:
                all_authors.add(a)

            books_data.append(
                {
                    "title": row["title"],
                    "authors": authors,
                    "series_name": row.get("series_name", ""),
                    "series_position": row.get("series_index", ""),
                    "isbn13": row.get("isbn13", ""),
                    "isbn10": row.get("isbn10", ""),
                    "publication_date": parse_month_year(row.get("publication_month_year", "")),
                    "distributor_royalty_rate": float(row.get("distribution_royalty_percent", 0)) / 100,
                    "handsold_royalty_rate": float(row.get("hand_sold_royalty_percent", 0)) / 100,
                    "cover_price": row.get("cover_price", "0.00"),
                    "print_cost": row.get("print_cost", "0.00"),
                    "cover_image": row.get("cover_image", "").strip(),
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
            "series_name": book["series_name"] if book["series_name"] else None,
            "series_position": book["series_position"] if book["series_position"] else None,
            "distributor_author_royalty_rate": book["distributor_royalty_rate"],
            "hand_sold_author_royalty_rate": book["handsold_royalty_rate"],
            "cover_price": book["cover_price"],
            "print_cost": book["print_cost"],
        }

        resp = session.post(f"{base_url}/api/books/", json=payload)

        if resp.status_code == 201:
            success_count += 1
            print(f"✓ Created: {book['title']}")
            book_obj = resp.json()

            if book["cover_image"]:
                 upload_cover_image(session, base_url, book_obj["id"], book["cover_image"])
        else:
            print(f"✗ Failed: {book['title']} - {resp.text}")

    print(f"Created {success_count} books.")
    return success_count


def import_sales(session, base_url, records_csv_path):
    print("\nImporting sales...")

    resp = session.get(f"{base_url}/api/books/")
    if resp.status_code != 200:
        print(resp.text)
        return 0

    data = resp.json()
    books = dict()
    # Handle pagination
    while True:
        results = data.get("results", data) if isinstance(data, dict) else data
        for b in results:
            if b.get("isbn_13"):
                 books[str(b["isbn_13"])] = b

        if isinstance(data, dict) and data.get("next"):
             resp = session.get(data["next"])
             data = resp.json()
        else:
             break

    isbn_to_book = books
    success_count = 0

    with open(records_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            isbn13 = row.get("isbn13")
            if not isbn13 or isbn13 not in isbn_to_book:
                print(f"⚠ Skipping sale for unknown ISBN: {isbn13}")
                continue

            book = isbn_to_book[isbn13]

            sale_date = parse_month_year(row.get("record_month_year", ""))
            quantity = int(row.get("units_sold", 0))
            royalty_paid = (row.get("royalty_paid", "n") or "n").lower() == "y"
            source = row.get("source", "distributor").lower()
            comment = row.get("comment", "")

            sale_data = {
                "book": book["id"],
                "date": sale_date,
                "quantity": quantity,
                "sale_source": source,
                "author_paid": royalty_paid,
                "comment": comment,
            }

            if source == "distributor":
                revenue_str = row.get("total_revenue", "").strip()
                if revenue_str:
                    sale_data["publisher_revenue"] = revenue_str
                else:
                    print(f"⚠ Skipping distributor sale for {isbn13} (Missing revenue)")
                    continue

            resp = session.post(f"{base_url}/api/sales/", json=sale_data)

            if resp.status_code == 201:
                success_count += 1
            else:
                 print(f"✗ Failed to create sale for {isbn13} on {sale_date}: {resp.text}")

    print(f"Created {success_count} sales records.")
    return success_count

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=BASE_URL)
    parser.add_argument("--username", default=USERNAME)
    parser.add_argument("--password", default=PASSWORD)
    parser.add_argument("--skip-books", action="store_true")
    parser.add_argument("--skip-sales", action="store_true")
    args = parser.parse_args()

    session = get_session(args.url, args.username, args.password)

    if not args.skip_books:
        import_books(
            session,
            args.url,
            BOOKS_CSV,
        )

    if not args.skip_sales:
        import_sales(session, args.url, RECORDS_CSV)


if __name__ == "__main__":
    main()
