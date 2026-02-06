import requests
import random
import datetime
import string
import sys

# Configuration
BASE_URL = "http://localhost:8000"
# Login credentials (matching entrypoint.sh defaults)
USERNAME = "admin"
PASSWORD = "password"

def get_session():
    """
    Log in and return a session with the auth cookie/token.
    This assumes session-based auth (standard Django login).
    """
    s = requests.Session()
    
    # 1. Get CSRF token (if needed, usually getting the login page or a dedicated csrf endpoint sets the cookie)
    # The provided backend has a specific csrf endpoint: /csrf
    # But usually API views with SessionAuthentication enforce CSRF.
    # Let's try to hit the CSRF endpoint first to set the cookie.
    try:
        csrf_resp = s.get(f"{BASE_URL}/api/csrf")
        csrf_resp.raise_for_status()
        # Django requires X-CSRFToken header for POST requests
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
    # Update CSRF token if it rotated after login
    if 'csrftoken' in s.cookies:
        s.headers.update({'X-CSRFToken': s.cookies['csrftoken']})
        
    return s

def get_or_create_author(session):
    """
    Ensure at least one author exists and return a list of author IDs.
    """
    print("Fetching authors...")
    resp = session.get(f"{BASE_URL}/api/authors/")
    if resp.status_code != 200:
        print(f"Failed to fetch authors: {resp.status_code}")
        sys.exit(1)
        
    data = resp.json()
    # Pagination check: 'results' key usually present if paginated
    authors = data.get('results', data) if isinstance(data, dict) else data
    
    if len(authors) < 5:
        needed = 5 - len(authors)
        print(f"Less than 5 authors found. Creating {needed} dummy authors...")
        for _ in range(needed):
            new_author = {
                "name": f"Auto Author {random.randint(1000, 9999)} - {random.choice(string.ascii_uppercase)}",
                "bio": "Created by automation script."
            }
            create_resp = session.post(f"{BASE_URL}/api/authors/", json=new_author)
            if create_resp.status_code != 201:
                print(f"Failed to create author: {create_resp.text}")
                # Don't exit, just continue with what we have
            else:
                authors.append(create_resp.json())
        
    return [a['id'] for a in authors]

def generate_isbn13():
    # Start with 978
    prefix = "978"
    # Generate 9 random digits
    core = "".join(random.choices(string.digits, k=9))
    # Calculate checksum (simple implementation or just random last digit if backend doesn't validate strictly)
    # Let's just generate a 13-digit string. The model has max_length=13.
    # It doesn't seem to enforce checksum validation in the model definition, just string length.
    return prefix + core + random.choice(string.digits)

def generate_books(session, author_ids, count=55):
    print(f"Generating {count} books...")
    
    success_count = 0
    url = f"{BASE_URL}/api/books/"
    
    for i in range(count):
        # Random data
        suffix = "".join(random.choices(string.ascii_uppercase, k=3))
        title = f"Automated Book {i+1} - {suffix}"
        
        # Random date in last 5 years
        start_date = datetime.date(2020, 1, 1)
        end_date = datetime.date.today()
        time_between_dates = end_date - start_date
        days_between_dates = time_between_dates.days
        random_number_of_days = random.randrange(days_between_dates)
        pub_date = start_date + datetime.timedelta(days=random_number_of_days)
        
        isbn13 = generate_isbn13()
        # Ensure uniqueness by appending/modifying if needed, but random is likely unique enough for 55 books.
        
        # Pick 1-2 authors
        num_authors = random.choice([1, 1, 2, 2, 3]) # Mostly 1 author
        selected_authors = random.sample(author_ids, min(len(author_ids), num_authors))
        
        # Construct payload
        # Structure based on BookCreateSerializer:
        # fields = ["title", "publication_date", "isbn_13", "isbn_10", "authors"]
        # authors = [{"author_id": id, "royalty_rate": ...}]
        
        authors_payload = []
        for auth_id in selected_authors:
            authors_payload.append({
                "author_id": auth_id,
                "royalty_rate": round(random.uniform(0.05, 0.20), 2) # 5% to 20%
            })
            
        payload = {
            "title": title,
            "publication_date": str(pub_date),
            "isbn_13": isbn13,
            "isbn_10": None, # Optional
            "authors": authors_payload
        }
        
        resp = session.post(url, json=payload)
        
        if resp.status_code == 201:
            success_count += 1
            sys.stdout.write(".")
            sys.stdout.flush()
        else:
            print(f"\nFailed to create book {i+1}: {resp.status_code} {resp.text}")
            
    print(f"\n\nSuccessfully created {success_count} books.")

def main():
    try:
        session = get_session()
        author_ids = get_or_create_author(session)
        generate_books(session, author_ids, count=55)
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to {BASE_URL}. Is the server running?")
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    main()
