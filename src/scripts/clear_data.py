#!/usr/bin/env python3
"""
Script to wipe all books, sales, and authors from the database.

Run:
  python3 src/scripts/clear_data.py --env local
  python3 src/scripts/clear_data.py --env prod
"""

import requests
import argparse
import sys

ENV_URLS = {
    "local": "http://localhost:8000",
    "prod": "https://vcm-51887.vm.duke.edu"
}
USERNAME = "admin"
PASSWORD = "password"


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


def fetch_all(session, url):
    """Fetch all records from a paginated endpoint."""
    results = []
    next_url = url
    while next_url:
        resp = session.get(next_url)
        if resp.status_code != 200:
            print(f"Failed to fetch {next_url}: {resp.status_code} {resp.text}")
            sys.exit(1)
        data = resp.json()
        if isinstance(data, list):
            results.extend(data)
            break
        results.extend(data.get("results", []))
        next_url = data.get("next")
    return results


def delete_all_sales(session, base_url):
    print("\nFetching sales...")
    sales = fetch_all(session, f"{base_url}/api/sales/")
    print(f"Found {len(sales)} sales records.")
    count = 0
    for sale in sales:
        resp = session.delete(f"{base_url}/api/sales/{sale['id']}/")
        if resp.status_code in (200, 204):
            count += 1
        else:
            print(f"  Failed to delete sale {sale['id']}: {resp.text}")
    print(f"Deleted {count} sales records.")
    return count


def delete_all_books(session, base_url):
    print("\nFetching books...")
    books = fetch_all(session, f"{base_url}/api/books/")
    print(f"Found {len(books)} books.")
    count = 0
    for book in books:
        resp = session.delete(f"{base_url}/api/books/{book['id']}/")
        if resp.status_code in (200, 204):
            count += 1
        else:
            print(f"  Failed to delete book {book['id']} ({book.get('title', '')}): {resp.text}")
    print(f"Deleted {count} books.")
    return count


def delete_all_authors(session, base_url):
    print("\nFetching authors...")
    authors = fetch_all(session, f"{base_url}/api/authors/")
    print(f"Found {len(authors)} authors.")
    count = 0
    for author in authors:
        resp = session.delete(f"{base_url}/api/authors/{author['id']}/")
        if resp.status_code in (200, 204):
            count += 1
        else:
            print(f"  Failed to delete author {author['id']} ({author.get('name', '')}): {resp.text}")
    print(f"Deleted {count} authors.")
    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", choices=["local", "prod"], default="local", help="Environment to clear")
    parser.add_argument("--url", help="Override base URL directly")
    parser.add_argument("--username", default=USERNAME)
    parser.add_argument("--password", default=PASSWORD)
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    base_url = args.url if args.url else ENV_URLS[args.env]

    if not args.yes:
        confirm = input(f"This will wipe ALL data from {base_url}. Type 'yes' to confirm: ")
        if confirm.strip().lower() != "yes":
            print("Aborted.")
            sys.exit(0)

    session = get_session(base_url, args.username, args.password)

    # Delete in dependency order: sales first, then books, then authors
    delete_all_sales(session, base_url)
    delete_all_books(session, base_url)
    delete_all_authors(session, base_url)

    print("\nDone. Database has been cleared.")


if __name__ == "__main__":
    main()
