#!/usr/bin/env python3
"""
Script to populate the production server with books and sales data.
Generates 55 books with varying numbers of authors (1-4) and royalty rates (5-25%),
then generates 60 sales entries with varying quantities and revenues.

Usage:
    python populate_prod.py
    
Configure BASE_URL below if needed.

Default: Connect to production server
python src/scripts/populate_prod.py

Custom options:
python src/scripts/populate_prod.py --url https://vcm-51984.vm.duke.edu --books 55 --sales 60

Skip book creation (only create sales):
python src/scripts/populate_prod.py --skip-books

Skip sales creation (only create books):
python src/scripts/populate_prod.py --skip-sales
"""
import requests
import random
import datetime
import string
import sys
import argparse

# Configuration - Update this to your production server URL
BASE_URL = "https://vcm-51984.vm.duke.edu"

# Login credentials (matching production defaults)
USERNAME = "admin"
PASSWORD = "password" # CHANGE THIS WHEN THE PROD PASSWORD CHANGES


def get_session(base_url):
    """
    Log in and return a session with the auth cookie/token.
    """
    s = requests.Session()
    
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
        "username": USERNAME,
        "password": PASSWORD
    }
    
    print(f"Logging in as {USERNAME} to {base_url}...")
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


def ensure_authors(session, base_url, min_authors=8):
    """
    Ensure at least min_authors authors exist and return a list of author objects.
    Creates additional authors with varied bios if needed.
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
    authors = data.get('results', data) if isinstance(data, dict) else data
    
    print(f"Found {len(authors)} existing authors.")
    
    if len(authors) < min_authors:
        needed = min_authors - len(authors)
        print(f"Creating {needed} additional authors...")
        
        author_names = [
            "Jane Austen Smith", "Charles Dickens Jr.", "Mark Twain III",
            "Virginia Woolf II", "Ernest Hemingway Jr.", "Gabriel García López",
            "Haruki Murakami II", "Toni Morrison Jr.", "Leo Tolstoy III",
            "Fyodor Dostoevsky II", "Maya Angelou Jr.", "Oscar Wilde III"
        ]
        
        bios = [
            "Award-winning author known for contemporary fiction.",
            "Bestselling mystery and thriller writer.",
            "Renowned academic and literary critic.",
            "Celebrated poet and essayist.",
            "International bestselling romance novelist.",
            "Pulitzer Prize-nominated journalist turned novelist.",
            "Distinguished professor and author of historical fiction.",
            "Independent author specializing in sci-fi and fantasy."
        ]
        
        for i in range(needed):
            name = author_names[i % len(author_names)] if i < len(author_names) else f"Author {random.randint(1000, 9999)}"
            # Add random suffix to ensure uniqueness
            name = f"{name} {random.choice(string.ascii_uppercase)}{random.randint(10, 99)}"
            
            new_author = {
                "name": name,
                "bio": random.choice(bios)
            }
            try:
                create_resp = session.post(f"{base_url}/api/authors/", json=new_author, verify=False)
            except:
                create_resp = session.post(f"{base_url}/api/authors/", json=new_author)
                
            if create_resp.status_code == 201:
                authors.append(create_resp.json())
                print(f"  Created author: {name}")
            else:
                print(f"  Failed to create author: {create_resp.text}")
    
    return authors


def generate_isbn13():
    """Generate a random valid-format ISBN-13."""
    prefix = random.choice(["978", "979"])
    core = "".join(random.choices(string.digits, k=9))
    return prefix + core + random.choice(string.digits)


def generate_isbn10():
    """Generate a random valid-format ISBN-10 (optional field)."""
    core = "".join(random.choices(string.digits, k=9))
    check = random.choice(string.digits + "X")
    return core + check


def generate_books(session, base_url, authors, count=55):
    """
    Generate books with varying numbers of authors and royalty rates.
    
    Distribution:
    - 1 author: ~30%
    - 2 authors: ~35%
    - 3 authors: ~25%
    - 4 authors: ~10%
    
    Royalty rates vary from 5% to 25%.
    """
    print(f"\n{'='*50}")
    print(f"Generating {count} books...")
    print(f"{'='*50}")
    
    success_count = 0
    url = f"{base_url}/api/books/"
    
    # Book title prefixes for variety
    genres = ["Mystery", "Romance", "Thriller", "Fantasy", "Historical", "Literary", 
              "Science Fiction", "Biography", "Self-Help", "Adventure", "Drama", "Comedy"]
    
    adjectives = ["Secret", "Lost", "Hidden", "Ancient", "Modern", "Final", "First", 
                  "Forgotten", "Eternal", "Silent", "Burning", "Frozen", "Golden"]
    
    nouns = ["Garden", "Kingdom", "Journey", "Legacy", "Promise", "Dream", "Memory",
             "Shadow", "Light", "River", "Mountain", "Ocean", "Forest", "City"]
    
    # Author count distribution: weighted towards 1-2 authors
    author_count_weights = [1, 1, 1, 2, 2, 2, 2, 3, 3, 4]
    
    for i in range(count):
        # Generate unique title
        genre = random.choice(genres)
        adj = random.choice(adjectives)
        noun = random.choice(nouns)
        suffix = random.randint(1, 999)
        title = f"The {adj} {noun}: A {genre} Novel #{suffix}"
        
        # Random publication date in last 5 years
        start_date = datetime.date(2020, 1, 1)
        end_date = datetime.date.today()
        days_range = (end_date - start_date).days
        pub_date = start_date + datetime.timedelta(days=random.randrange(days_range))
        
        isbn13 = generate_isbn13()
        # 50% chance of having ISBN-10
        isbn10 = generate_isbn10() if random.random() > 0.5 else None
        
        # Pick number of authors (weighted distribution)
        num_authors = random.choice(author_count_weights)
        num_authors = min(num_authors, len(authors))  # Can't have more authors than available
        selected_authors = random.sample(authors, num_authors)
        
        # Generate authors payload with varying royalty rates
        # Royalty rates: 5% to 25% with more variation
        # API expects author_name (not author_id)
        authors_payload = []
        for author in selected_authors:
            # Generate varied royalty rates
            # Primary author often gets higher rate
            if len(authors_payload) == 0:  # First/primary author
                base_rate = random.uniform(0.12, 0.25)  # 12-25%
            else:  # Co-authors get lower rates
                base_rate = random.uniform(0.05, 0.15)  # 5-15%
            
            # Round to 2 decimal places
            royalty_rate = round(base_rate, 2)
            
            authors_payload.append({
                "author_name": author['name'],
                "royalty_rate": royalty_rate
            })
        
        payload = {
            "title": title,
            "publication_date": str(pub_date),
            "isbn_13": isbn13,
            "isbn_10": isbn10,
            "authors": authors_payload
        }
        
        try:
            resp = session.post(url, json=payload, verify=False)
        except:
            resp = session.post(url, json=payload)
        
        if resp.status_code == 201:
            success_count += 1
            book_data = resp.json()
            author_info = ", ".join([f"{a['author_name'][:15]} @ {a['royalty_rate']*100:.0f}%" for a in authors_payload])
            print(f"  [{success_count:2d}] Created: {title[:40]}... ({num_authors} author(s): {author_info})")
        else:
            print(f"  [FAIL] {title[:40]}: {resp.status_code} - {resp.text[:100]}")
    
    print(f"\n✓ Successfully created {success_count}/{count} books.")
    return success_count


def generate_sales(session, base_url, count=60):
    """
    Generate sales with varying quantities, revenues, and royalty payments.
    
    - Quantities: 1-500 units
    - Unit prices: $5-$75
    - Mixed payment statuses for authors
    """
    print(f"\n{'='*50}")
    print(f"Generating {count} sales...")
    print(f"{'='*50}")
    
    # First fetch all books
    print("Fetching books for sales generation...")
    try:
        resp = session.get(f"{base_url}/api/books/?all=true", verify=False)
    except:
        resp = session.get(f"{base_url}/api/books/?all=true")
        
    if resp.status_code != 200:
        print(f"Failed to fetch books: {resp.status_code}")
        return 0
        
    data = resp.json()
    books = data.get('results', data) if isinstance(data, dict) else data
    
    if not books:
        print("No books found. Please generate books first.")
        return 0
    
    print(f"Found {len(books)} books to create sales for.")
    
    sales_data = []
    
    for i in range(count):
        book = random.choice(books)
        book_id = book['id']
        
        # Parse publication date to ensure sale date is after
        try:
            pub_date = datetime.datetime.strptime(book['publication_date'], '%Y-%m-%d').date()
        except:
            pub_date = datetime.date(2020, 1, 1)
        
        # Sale date: between publication date and today
        end_date = datetime.date.today()
        if pub_date >= end_date:
            sale_date = end_date
        else:
            days_range = (end_date - pub_date).days
            if days_range > 0:
                sale_date = pub_date + datetime.timedelta(days=random.randrange(days_range))
            else:
                sale_date = end_date
        
        # Varied quantities with distribution (more smaller sales)
        quantity_weights = [(1, 50), (51, 150), (151, 300), (301, 500)]
        quantity_range = random.choices(quantity_weights, weights=[50, 30, 15, 5])[0]
        quantity = random.randint(quantity_range[0], quantity_range[1])
        
        # Varied unit prices
        price_tiers = [(5, 15), (15, 30), (30, 50), (50, 75)]
        price_range = random.choices(price_tiers, weights=[20, 40, 30, 10])[0]
        unit_price = round(random.uniform(price_range[0], price_range[1]), 2)
        
        # Calculate revenue
        revenue = round(unit_price * quantity, 2)
        
        # Generate author payment status (varied)
        author_paid_map = {}
        if 'authors' in book:
            for ab in book['authors']:
                # 40% paid, 30% unpaid, 30% based on revenue size
                roll = random.random()
                if roll < 0.4:
                    is_paid = True
                elif roll < 0.7:
                    is_paid = False
                else:
                    # Higher revenue = more likely to be paid
                    is_paid = revenue > 1000
                author_paid_map[str(ab['author_id'])] = is_paid
        
        sale_obj = {
            "book": book_id,
            "date": str(sale_date),
            "quantity": quantity,
            "publisher_revenue": str(revenue),
            "author_paid": author_paid_map
        }
        sales_data.append(sale_obj)
    
    # Bulk create sales
    url = f"{base_url}/api/sale/createmany"
    print(f"Posting {len(sales_data)} sales...")
    
    try:
        resp = session.post(url, json=sales_data, verify=False)
    except:
        resp = session.post(url, json=sales_data)
    
    if resp.status_code == 201:
        print(f"\n✓ Successfully created {count} sales.")
        
        # Print some stats
        total_revenue = sum(float(s['publisher_revenue']) for s in sales_data)
        avg_quantity = sum(s['quantity'] for s in sales_data) / len(sales_data)
        print(f"  Total revenue: ${total_revenue:,.2f}")
        print(f"  Average quantity per sale: {avg_quantity:.1f}")
        return count
    else:
        print(f"Failed to create sales: {resp.status_code} {resp.text}")
        return 0


def get_session_with_creds(base_url, username, password):
    """
    Log in and return a session with the auth cookie/token.
    """
    s = requests.Session()
    
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


def main():
    parser = argparse.ArgumentParser(description='Populate production server with books and sales data.')
    parser.add_argument('--url', default=BASE_URL, help=f'Base URL of the server (default: {BASE_URL})')
    parser.add_argument('--books', type=int, default=55, help='Number of books to create (default: 55)')
    parser.add_argument('--sales', type=int, default=60, help='Number of sales to create (default: 60)')
    parser.add_argument('--username', default=USERNAME, help=f'Login username (default: {USERNAME})')
    parser.add_argument('--password', default=PASSWORD, help=f'Login password (default: {PASSWORD})')
    parser.add_argument('--skip-books', action='store_true', help='Skip book generation')
    parser.add_argument('--skip-sales', action='store_true', help='Skip sales generation')
    
    args = parser.parse_args()
    
    print(f"\n{'#'*60}")
    print(f"# Production Data Population Script")
    print(f"# Target: {args.url}")
    print(f"# Books: {args.books}, Sales: {args.sales}")
    print(f"{'#'*60}\n")
    
    try:
        # Suppress SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        session = get_session(args.url)
        
        # Ensure we have enough authors for varied book authorship
        authors = ensure_authors(session, args.url, min_authors=8)
        
        if not args.skip_books:
            generate_books(session, args.url, authors, count=args.books)
        else:
            print("Skipping book generation.")
        
        if not args.skip_sales:
            generate_sales(session, args.url, count=args.sales)
        else:
            print("Skipping sales generation.")
        
        print(f"\n{'#'*60}")
        print("# Population complete!")
        print(f"{'#'*60}\n")
        
    except requests.exceptions.ConnectionError as e:
        print(f"Error: Could not connect to {args.url}. Is the server running?")
        print(f"Details: {e}")
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()
