import requests
import random
import datetime
import sys

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "password"

def get_session():
    """
    Log in and return a session with the auth cookie/token.
    """
    s = requests.Session()
    
    # 1. CSRF
    try:
        csrf_resp = s.get(f"{BASE_URL}/api/csrf")
        csrf_resp.raise_for_status()
        if 'csrftoken' in s.cookies:
            s.headers.update({'X-CSRFToken': s.cookies['csrftoken']})
    except Exception as e:
        print(f"Warning: Could not fetch CSRF token: {e}")

    # 2. Login
    login_url = f"{BASE_URL}/api/user/login"
    payload = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    print(f"Logging in as {USERNAME}...")
    resp = s.post(login_url, json=payload)
    
    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code} {resp.text}")
        sys.exit(1)
        
    print("Login successful.")
    if 'csrftoken' in s.cookies:
        s.headers.update({'X-CSRFToken': s.cookies['csrftoken']})
        
    return s

def get_books(session):
    """
    Fetch all books with their author details.
    """
    print("Fetching books...")
    # Using ?all=true based on BookListCreateView implementation to get all results
    resp = session.get(f"{BASE_URL}/api/books/?all=true")
    if resp.status_code != 200:
        print(f"Failed to fetch books: {resp.status_code}")
        sys.exit(1)
        
    data = resp.json()
    books = data.get('results', data) if isinstance(data, dict) else data
    
    if not books:
        print("No books found. Please run populate_books.py first.")
        sys.exit(1)
        
    print(f"Found {len(books)} books.")
    # Return the full book objects so we can access their authors
    return books

def generate_sales(session, books, count=100):
    print(f"Generating {count} sales...")
    
    sales_data = []
    
    for _ in range(count):
        book = random.choice(books)
        book_id = book['id']
        
        # Random date in last 2 years
        start_date = datetime.date.today() - datetime.timedelta(days=730)
        end_date = datetime.date.today()
        time_between_dates = end_date - start_date
        days_between_dates = time_between_dates.days
        random_number_of_days = random.randrange(days_between_dates)
        sale_date = start_date + datetime.timedelta(days=random_number_of_days)
        
        # Random quantity 1-100
        quantity = random.randint(1, 100)
        
        # Random unit price 10-50
        unit_price = random.uniform(10, 50)
        
        # Revenue
        revenue = round(unit_price * quantity, 2)
        
        # Randomize author payment status
        # book['authors'] is a list of AuthorBook objects: [{'author_id': 1, ...}, ...]
        author_paid_map = {}
        if 'authors' in book:
            for ab in book['authors']:
                # 50% chance of being paid
                is_paid = random.choice([True, False])
                author_paid_map[str(ab['author_id'])] = is_paid
        
        sale_obj = {
            "book": book_id,
            "date": str(sale_date),
            "quantity": quantity,
            "publisher_revenue": str(revenue),
            "author_paid": author_paid_map
        }
        sales_data.append(sale_obj)
        
    # Bulk create
    url = f"{BASE_URL}/api/sale/createmany"
    print(f"Posting {len(sales_data)} sales to {url}...")
    
    resp = session.post(url, json=sales_data)
    
    if resp.status_code == 201:
        print("Successfully created 100 sales.")
    else:
        print(f"Failed to create sales: {resp.status_code} {resp.text}")

def main():
    try:
        session = get_session()
        book_ids = get_books(session)
        generate_sales(session, book_ids, count=100)
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to {BASE_URL}. Is the server running?")
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    main()
