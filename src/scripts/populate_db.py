#!/usr/bin/env python3
"""
Populate the database with dummy books and sales.

Usage:
    python populate_db.py                       # defaults: 50 authors, 150 books, 500 sales
    python populate_db.py --books 20 --sales 100
    python populate_db.py --authors 10 --books 0 --sales 0   # authors only
"""

import argparse
import datetime
import random
import string
import sys

import requests

# ── Configuration ──────────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "458group2"

SALE_SOURCES = ["distributor", "handsold"]

SAMPLE_COMMENTS = [
    None,
    "",
    "Bulk school order",
    "Holiday promotion",
    "Author event signing",
    "Online flash sale",
    "Return / adjustment",
    "Library acquisition",
    "Book fair",
    "Pre-order fulfillment",
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_session():
    """Log in and return a requests.Session with auth cookies."""
    s = requests.Session()

    # CSRF
    try:
        csrf_resp = s.get(f"{BASE_URL}/api/csrf")
        csrf_resp.raise_for_status()
        if "csrftoken" in s.cookies:
            s.headers.update({"X-CSRFToken": s.cookies["csrftoken"]})
    except Exception as e:
        print(f"Warning: Could not fetch CSRF token: {e}")

    # Login
    print(f"Logging in as {USERNAME}...")
    resp = s.post(f"{BASE_URL}/api/user/login", json={"username": USERNAME, "password": PASSWORD})
    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code} {resp.text}")
        sys.exit(1)
    print("Login successful.")

    if "csrftoken" in s.cookies:
        s.headers.update({"X-CSRFToken": s.cookies["csrftoken"]})
    return s


def ensure_authors(session, min_count=50):
    """Make sure at least `min_count` authors exist; create any that are missing."""
    print("Fetching authors...")
    resp = session.get(f"{BASE_URL}/api/authors/")
    if resp.status_code != 200:
        print(f"Failed to fetch authors: {resp.status_code}")
        sys.exit(1)

    data = resp.json()
    authors = data.get("results", data) if isinstance(data, dict) else data

    needed = max(0, min_count - len(authors))
    if needed:
        print(f"Creating {needed} authors...")
        for _ in range(needed):
            uid = random.randint(10000, 99999)
            name = f"Auto Author {uid}-{random.choice(string.ascii_uppercase)}"
            email = f"author{uid}@example.com"
            r = session.post(f"{BASE_URL}/api/authors/", json={"name": name, "email": email})
            if r.status_code == 201:
                authors.append(r.json())
                sys.stdout.write(".")
                sys.stdout.flush()
            else:
                print(f"\nFailed to create author: {r.text}")
        if needed:
            print()

    print(f"Total authors: {len(authors)}")
    return authors


def generate_isbn13():
    """Generate a random 13-digit ISBN-like string starting with 978."""
    core = "".join(random.choices(string.digits, k=9))
    return "978" + core + random.choice(string.digits)


def generate_asin():
    """Generate a random 10-character Amazon ASIN starting with B0."""
    return "B0" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


def generate_books(session, authors, count=150):
    """Create `count` books via the API."""
    if count <= 0:
        return
    print(f"Creating {count} books...")

    success = 0
    url = f"{BASE_URL}/api/books/"

    for i in range(count):
        suffix = "".join(random.choices(string.ascii_uppercase, k=3))
        title = f"Automated Book {i + 1} - {suffix}"

        # Random publication date in last 5 years
        start = datetime.date(2020, 1, 1)
        end = datetime.date.today()
        pub_date = start + datetime.timedelta(days=random.randrange((end - start).days))

        # Pick 1 author
        selected = random.sample(authors, 1)

        payload = {
            "title": title,
            "publication_date": pub_date.strftime("%Y-%m"),
            "isbn_13": generate_isbn13(),
            "isbn_10": None,
            "amazon_asin_ebook": generate_asin() if random.random() < 0.5 else None,
            "author_id": selected[0]["id"] if "id" in selected[0] else selected[0].get("author_id"),
            "distributor_author_royalty_rate": str(round(random.uniform(0.05, 0.20), 2)),
            "hand_sold_author_royalty_rate": "0.20",
            "cover_price": str(round(random.uniform(15.00, 35.00), 2)),
            "print_cost": str(round(random.uniform(3.00, 10.00), 2)),
        }

        resp = session.post(url, json=payload)
        if resp.status_code == 201:
            success += 1
            sys.stdout.write(".")
            sys.stdout.flush()
        else:
            print(f"\nFailed to create book {i + 1}: {resp.status_code} {resp.text}")

    print(f"\nSuccessfully created {success}/{count} books.")


def fetch_books(session):
    """Fetch all books (needed for generating sales)."""
    print("Fetching books...")
    resp = session.get(f"{BASE_URL}/api/books/?all=true")
    if resp.status_code != 200:
        print(f"Failed to fetch books: {resp.status_code}")
        sys.exit(1)

    data = resp.json()
    books = data.get("results", data) if isinstance(data, dict) else data

    if not books:
        print("No books found — cannot generate sales.")
        sys.exit(1)

    print(f"Found {len(books)} books.")
    return books


def generate_sales(session, books, count=500):
    """Create `count` sales via the bulk endpoint."""
    if count <= 0:
        return
    print(f"Generating {count} sales...")

    distributors = ["Ingram Spark", "Amazon", "Other"]
    formats = ["print", "ebook", "kindle unlimited"]
    currencies = [
        ("USD", 1.0),
        ("GBP", 1.27),
        ("EUR", 1.08),
        ("CAD", 0.74),
        ("AUD", 0.65),
        ("JPY", 0.0066),
        ("INR", 0.012),
    ]

    sales_data = []
    for _ in range(count):
        book = random.choice(books)

        # Sale date: random month in last 2 years, but not before publication
        start = datetime.date.today() - datetime.timedelta(days=730)
        end = datetime.date.today()
        sale_date = start + datetime.timedelta(days=random.randrange((end - start).days))

        # Ensure sale is not before publication
        pub = book.get("publication_date", "")
        if pub:
            try:
                pub_parts = pub.split("-")
                pub_date = datetime.date(int(pub_parts[0]), int(pub_parts[1]), 1)
                if sale_date < pub_date:
                    sale_date = pub_date
            except (ValueError, IndexError):
                pass

        sale_source = random.choice(SALE_SOURCES)

        # Distributor field
        distributor = random.choice(distributors) if sale_source == "distributor" else None

        # Choose a valid format
        if sale_source == "handsold":
            sale_format = "print"
        else:
            if distributor == "Ingram Spark":
                sale_format = "print"
            elif distributor == "Amazon":
                sale_format = random.choice(["print", "ebook", "kindle unlimited"])
            else:
                sale_format = random.choice(["print", "ebook"])

        # Determine quantity and KENP based on format
        if sale_format == "kindle unlimited":
            quantity = None
            kenp = random.randint(100, 5000)
        else:
            quantity = random.randint(1, 100)
            kenp = None

        # Revenue with occasional non-USD currency for distributor sales
        unit_price = random.uniform(10, 50)
        qty_for_calc = quantity if quantity else random.randint(1, 20)
        currency_code, exchange_rate = ("USD", 1.0)
        publisher_revenue_original = None

        if sale_source == "distributor" and random.random() < 0.3:
            # 30% of distributor sales are in foreign currency
            currency_code, exchange_rate = random.choice(currencies[1:])  # skip USD
            publisher_revenue_original = round(unit_price * qty_for_calc, 2)
            revenue = round(publisher_revenue_original * exchange_rate, 2)
        else:
            revenue = round(unit_price * qty_for_calc, 2)

        author_paid = random.choice([True, False])
        comment = random.choice(SAMPLE_COMMENTS)

        sale_obj = {
            "book": book["id"],
            "date": sale_date.strftime("%Y-%m"),
            "quantity": quantity,
            "publisher_revenue": str(revenue),
            "sale_source": sale_source,
            "author_paid": author_paid,
            "comment": comment,
            "format": sale_format,
            "currency": currency_code,
        }

        if distributor:
            sale_obj["distributor"] = distributor
        if publisher_revenue_original is not None:
            sale_obj["publisher_revenue_original"] = str(publisher_revenue_original)
        if kenp is not None:
            sale_obj["kenp"] = kenp

        sales_data.append(sale_obj)

    url = f"{BASE_URL}/api/sales/create-many/"
    print(f"Posting {len(sales_data)} sales...")
    resp = session.post(url, json=sales_data)
    if resp.status_code == 201:
        print(f"Successfully created {count} sales.")
    else:
        print(f"Failed to create sales: {resp.status_code} {resp.text}")


# Books referenced in data/ev2/Ingram-202509.csv
# Note: The "Author" column in the CSV is ignored during import — only ISBN matters.
# We assign existing system authors to these books.
INGRAM_BOOKS = [
    {"isbn_13": "9781473619814", "title": "The Long Way to a Small, Angry Planet",
     "pub_date": "2015-08", "royalty_rate": 0.10},
    {"isbn_13": "9780062569400", "title": "A Closed and Common Orbit",
     "pub_date": "2016-10", "royalty_rate": 0.10},
    {"isbn_13": "9780062699220", "title": "Record of a Spaceborn Few",
     "pub_date": "2018-07", "royalty_rate": 0.10},
    {"isbn_13": "9780062936042", "title": "The Galaxy, and the Ground Within",
     "pub_date": "2021-04", "royalty_rate": 0.10},
    {"isbn_13": "9780765397539", "title": "All Systems Red",
     "pub_date": "2017-05", "royalty_rate": 0.15},
    {"isbn_13": "9781250186928", "title": "Artificial Condition",
     "pub_date": "2018-05", "royalty_rate": 0.15},
    {"isbn_13": "9781250191786", "title": "Ancillary Justice",
     "pub_date": "2013-10", "royalty_rate": 0.12},
    {"isbn_13": "9780316565172", "title": "Ancillary Justice (Trade Paperback)",
     "pub_date": "2013-10", "royalty_rate": 0.12},
]


def ensure_ingram_books(session, authors):
    """Create the books referenced in the sample Ingram CSV (skip if ISBN already exists)."""
    print("Ensuring Ingram CSV sample books exist...")

    url = f"{BASE_URL}/api/books/"
    created = 0
    skipped = 0

    for i, entry in enumerate(INGRAM_BOOKS):
        # Pick an existing author (round-robin through available authors)
        author = authors[i % len(authors)]
        payload = {
            "title": entry["title"],
            "publication_date": entry["pub_date"],
            "isbn_13": entry["isbn_13"],
            "isbn_10": None,
            "author_id": author["id"] if "id" in author else author.get("author_id"),
            "distributor_author_royalty_rate": str(entry["royalty_rate"]),
            "hand_sold_author_royalty_rate": "0.20",
            "cover_price": "20.00",
            "print_cost": "10.00",
        }
        resp = session.post(url, json=payload)
        if resp.status_code == 201:
            created += 1
            sys.stdout.write(".")
            sys.stdout.flush()
        elif resp.status_code == 400:
            err_text = resp.text[:300]
            if "isbn_13" in err_text.lower() and ("unique" in err_text.lower() or "already exists" in err_text.lower()):
                skipped += 1
            else:
                print(f"\n  Rejected '{entry['title']}' ({entry['isbn_13']}): {err_text}")
        else:
            print(f"\n  Failed '{entry['title']}' ({entry['isbn_13']}): HTTP {resp.status_code} {resp.text}")

    if created:
        print()
    print(f"Ingram books: {created} created, {skipped} already existed.")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Populate the database with dummy data.")
    parser.add_argument("--authors", type=int, default=50, help="Minimum number of authors (default: 50)")
    parser.add_argument("--books", type=int, default=150, help="Number of books to create (default: 150)")
    parser.add_argument("--sales", type=int, default=500, help="Number of sales to create (default: 500)")
    args = parser.parse_args()

    try:
        session = get_session()

        authors = ensure_authors(session, min_count=args.authors)

        # Always create Ingram CSV sample books (using existing authors)
        ensure_ingram_books(session, authors)

        if args.books > 0:
            generate_books(session, authors, count=args.books)

        if args.sales > 0:
            books = fetch_books(session)
            generate_sales(session, books, count=args.sales)

        print("\nDone!")
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to {BASE_URL}. Is the server running?")
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()

