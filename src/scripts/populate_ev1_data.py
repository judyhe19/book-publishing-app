#!/usr/bin/env python3
"""
Script to populate the production database with EV1 review data from CSV files.

Usage:
    python populate_ev1_data.py

Configure BASE_URL, USERNAME, and PASSWORD below if needed.

Default: Connect to production server
    python src/scripts/populate_ev1_data.py

Custom options:
    python src/scripts/populate_ev1_data.py --url https://vcm-51984.vm.duke.edu
    python src/scripts/populate_ev1_data.py --skip-books  # Only import sales
    python src/scripts/populate_ev1_data.py --skip-sales  # Only import books
"""
import csv
import requests
import argparse
import sys
import os
from datetime import datetime

# Configuration - Update these to match your production server
BASE_URL = "https://vcm-51984.vm.duke.edu"
USERNAME = "admin"
PASSWORD = "password"  # CHANGE THIS WHEN THE PROD PASSWORD CHANGES

# CSV file paths (relative to project root)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
BOOKS_CSV = os.path.join(PROJECT_ROOT, "data/ev1-review-data/books.csv")
RECORDS_CSV = os.path.join(PROJECT_ROOT, "data/ev1-review-data/records.csv")


def get_session(base_url, username, password):
    """
    Log in and return a session with the auth cookie/token.
    """
    s = requests.Session()
    
    # Suppress SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # 1. Get CSRF token
    try:
        csrf_resp = s.get(f"{base_url}/api/csrf", verify=True)
        csrf_resp.raise_for_status()
        if 'csrftoken' in s.cookies:
            s.headers.update({'X-CSRFToken': s.cookies['csrftoken']})
    except requests.exceptions.SSLError:
        print("Warning: SSL verification failed. Retrying without verification...")
        s = requests.Session()
        csrf_resp = s.get(f"{base_url}/api/csrf", verify=False)
        if 'csrftoken' in s.cookies:
            s.headers.update({'X-CSRFToken': s.cookies['csrftoken']})
    except Exception as e:
        print(f"Warning: Could not fetch CSRF token: {e}")

    # 2. Login
    login_url = f"{base_url}/api/user/login"
    payload = {
        "username": username,
        "password": password
    }
    
    print(f"Logging in as {username} to {base_url}...")
    try:
        resp = s.post(login_url, json=payload, verify=True)
    except requests.exceptions.SSLError:
        resp = s.post(login_url, json=payload, verify=False)
    
    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code} {resp.text}")
        sys.exit(1)
        
    print("Login successful.")
    # Update CSRF token if it rotated after login
    if 'csrftoken' in s.cookies:
        s.headers.update({'X-CSRFToken': s.cookies['csrftoken']})
        
    return s


def parse_date(date_str):
    """
    Parse date string in MM/YYYY format and return YYYY-MM-DD format.
    Defaults to first day of month.
    """
    try:
        # Handle MM/YYYY format
        if '/' in date_str and len(date_str.split('/')) == 2:
            month, year = date_str.split('/')
            return f"{year}-{month.zfill(2)}-01"
        # Handle other formats
        return date_str
    except Exception as e:
        print(f"Warning: Could not parse date '{date_str}': {e}")
        return date_str


def ensure_authors(session, base_url, author_names):
    """
    Ensure authors exist in the database and return a mapping of name -> author object.
    Creates authors if they don't exist.
    """
    print("Fetching existing authors...")
    try:
        resp = session.get(f"{base_url}/api/authors/?all=true", verify=False)
    except:
        resp = session.get(f"{base_url}/api/authors/?all=true")
        
    if resp.status_code != 200:
        print(f"Failed to fetch authors: {resp.status_code}")
        sys.exit(1)
        
    data = resp.json()
    existing_authors = data.get('results', data) if isinstance(data, dict) else data
    
    # Create name -> author mapping (case-insensitive)
    author_map = {a['name'].lower(): a for a in existing_authors}
    
    # Find authors that need to be created
    for name in author_names:
        if name.lower() not in author_map:
            print(f"  Creating author: {name}")
            new_author = {
                "name": name,
                "bio": ""
            }
            try:
                create_resp = session.post(f"{base_url}/api/authors/", json=new_author, verify=False)
            except:
                create_resp = session.post(f"{base_url}/api/authors/", json=new_author)
                
            if create_resp.status_code == 201:
                author_obj = create_resp.json()
                author_map[name.lower()] = author_obj
            else:
                print(f"  Failed to create author '{name}': {create_resp.text}")
    
    return author_map


def import_books(session, base_url, books_csv_path):
    """
    Import books from CSV file.
    """
    print(f"\n{'='*50}")
    print(f"Importing books from {books_csv_path}")
    print(f"{'='*50}")
    
    # Read CSV and collect all author names first
    books_data = []
    all_authors = set()
    
    with open(books_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get('title'):
                continue
            
            # Parse authors (may be comma-separated for multiple authors)
            author_str = row.get('author', '')
            # Handle quoted multi-author strings like "Neil Gaiman, Terry Pratchett"
            authors = [a.strip() for a in author_str.split(',')]
            
            for author in authors:
                if author:
                    all_authors.add(author)
            
            books_data.append({
                'title': row['title'],
                'authors': authors,
                'isbn13': row.get('isbn13', ''),
                'isbn10': row.get('isbn10', ''),
                'publication_date': parse_date(row.get('publication_date', '')),
                'royalty_percent': float(row.get('royalty_percent', 0.1))
            })
    
    print(f"Found {len(books_data)} books and {len(all_authors)} unique authors in CSV.")
    
    # Ensure all authors exist
    author_map = ensure_authors(session, base_url, all_authors)
    
    # Create books
    success_count = 0
    url = f"{base_url}/api/books/"
    
    for book in books_data:
        # Build authors payload with royalty rates
        authors_payload = []
        royalty_per_author = book['royalty_percent'] / len(book['authors']) if book['authors'] else 0
        
        for author_name in book['authors']:
            if author_name and author_name.lower() in author_map:
                authors_payload.append({
                    "author_name": author_name,
                    "royalty_rate": book['royalty_percent']  # Each author gets the full royalty rate from CSV
                })
        
        payload = {
            "title": book['title'],
            "publication_date": book['publication_date'],
            "isbn_13": book['isbn13'],
            "isbn_10": book['isbn10'] if book['isbn10'] else None,
            "authors": authors_payload
        }
        
        try:
            resp = session.post(url, json=payload, verify=False)
        except:
            resp = session.post(url, json=payload)
        
        if resp.status_code == 201:
            success_count += 1
            print(f"  ✓ Created: {book['title']}")
        else:
            print(f"  ✗ Failed: {book['title']} - {resp.status_code}: {resp.text[:100]}")
    
    print(f"\n✓ Successfully created {success_count}/{len(books_data)} books.")
    return success_count


def import_sales(session, base_url, records_csv_path):
    """
    Import sales records from CSV file.
    """
    print(f"\n{'='*50}")
    print(f"Importing sales from {records_csv_path}")
    print(f"{'='*50}")
    
    # First, fetch all books to build ISBN -> book mapping
    print("Fetching books...")
    try:
        resp = session.get(f"{base_url}/api/books/?all=true", verify=False)
    except:
        resp = session.get(f"{base_url}/api/books/?all=true")
        
    if resp.status_code != 200:
        print(f"Failed to fetch books: {resp.status_code}")
        return 0
        
    data = resp.json()
    books = data.get('results', data) if isinstance(data, dict) else data
    
    # Build ISBN-13 -> book mapping
    isbn_to_book = {}
    for book in books:
        if book.get('isbn_13'):
            isbn_to_book[book['isbn_13']] = book
    
    print(f"Found {len(books)} books in database.")
    
    # Read sales CSV
    sales_data = []
    skipped = 0
    
    with open(records_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            isbn13 = row.get('isbn13', '')
            if not isbn13:
                continue
                
            if isbn13 not in isbn_to_book:
                print(f"  ⚠ Book not found for ISBN-13: {isbn13}")
                skipped += 1
                continue
            
            book = isbn_to_book[isbn13]
            
            # Parse sale data
            sale_date = parse_date(row.get('record_date', ''))
            quantity = int(row.get('units_sold', 0))
            revenue = float(row.get('total_revenue', 0))
            royalty_paid = row.get('royalty_paid', 'n').lower() == 'y'
            
            # Build author_paid map (all authors get same paid status)
            author_paid_map = {}
            if 'authors' in book:
                for ab in book['authors']:
                    author_paid_map[str(ab['author_id'])] = royalty_paid
            
            sales_data.append({
                "book": book['id'],
                "date": sale_date,
                "quantity": quantity,
                "publisher_revenue": str(revenue),
                "author_paid": author_paid_map
            })
    
    if skipped > 0:
        print(f"⚠ Skipped {skipped} sales records due to missing books.")
    
    if not sales_data:
        print("No sales records to import.")
        return 0
    
    print(f"Importing {len(sales_data)} sales records...")
    
    # Bulk create sales
    url = f"{base_url}/api/sale/createmany"
    
    try:
        resp = session.post(url, json=sales_data, verify=False)
    except:
        resp = session.post(url, json=sales_data)
    
    if resp.status_code == 201:
        print(f"\n✓ Successfully created {len(sales_data)} sales records.")
        
        # Print some stats
        total_revenue = sum(float(s['publisher_revenue']) for s in sales_data)
        total_units = sum(s['quantity'] for s in sales_data)
        print(f"  Total revenue: ${total_revenue:,.2f}")
        print(f"  Total units sold: {total_units:,}")
        return len(sales_data)
    else:
        print(f"Failed to create sales: {resp.status_code} {resp.text}")
        return 0


def main():
    parser = argparse.ArgumentParser(description='Import EV1 review data (books and sales) from CSV files.')
    parser.add_argument('--url', default=BASE_URL, help=f'Base URL of the server (default: {BASE_URL})')
    parser.add_argument('--username', default=USERNAME, help=f'Login username (default: {USERNAME})')
    parser.add_argument('--password', default=PASSWORD, help=f'Login password (default: {PASSWORD})')
    parser.add_argument('--books-csv', default=BOOKS_CSV, help=f'Path to books CSV file')
    parser.add_argument('--records-csv', default=RECORDS_CSV, help=f'Path to sales records CSV file')
    parser.add_argument('--skip-books', action='store_true', help='Skip book import')
    parser.add_argument('--skip-sales', action='store_true', help='Skip sales import')
    
    args = parser.parse_args()
    
    print(f"\n{'#'*60}")
    print(f"# EV1 Review Data Import Script")
    print(f"# Target: {args.url}")
    print(f"# Books CSV: {args.books_csv}")
    print(f"# Records CSV: {args.records_csv}")
    print(f"{'#'*60}\n")
    
    # Verify CSV files exist
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
        
    except requests.exceptions.ConnectionError as e:
        print(f"Error: Could not connect to {args.url}. Is the server running?")
        print(f"Details: {e}")
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()
