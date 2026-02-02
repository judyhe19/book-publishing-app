import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from bookapp.models import Book, Author, AuthorBook

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(username="u1", password="pass12345")


@pytest.fixture
def other_user():
    return User.objects.create_user(username="u2", password="pass12345")


@pytest.fixture
def authed_client(api_client, user):
    # bypasses login endpoint; best practice for API tests
    api_client.force_authenticate(user=user)
    return api_client


def make_author(name="Frank Herbert"):
    return Author.objects.create(name=name)


def make_book(*, publisher_user, isbn_13, title="T", authors=None):
    """
    Creates a Book and (optionally) attaches authors via the AuthorBook through table.
    authors: list of tuples [(Author, royalty_rate_str), ...]
    """
    book = Book.objects.create(
        title=title,
        publication_date="2000-01-01",
        isbn_13=isbn_13,
        isbn_10=None,
        total_sales_to_date=0,
        publisher_user=publisher_user,
    )

    if authors:
        for author, royalty_rate in authors:
            AuthorBook.objects.create(
                book=book,
                author=author,
                royalty_rate=royalty_rate,
            )

    return book


def test_get_books_requires_auth(api_client):
    resp = api_client.get("/api/books/")
    # DRF usually returns 401 for unauthenticated; sometimes 403 depending on settings
    assert resp.status_code in (401, 403)


def test_post_creates_book_sets_owner_and_ignores_total_sales(authed_client, user):
    a1 = make_author()

    payload = {
        "title": "Dune",
        "publication_date": "1965-08-01",
        "isbn_13": "9780441172719",
        "isbn_10": "0441172717",
        "total_sales_to_date": 999,  # should be ignored due to read_only_fields
        "authors": [
            {"author_id": a1.id, "royalty_rate": "0.15"},
        ],
        # publisher_user intentionally omitted (read-only)
    }

    resp = authed_client.post("/api/books/", payload, format="json")
    assert resp.status_code == 201, resp.content

    created_id = resp.data["id"]
    book = Book.objects.get(id=created_id)

    # owner forced server-side
    assert book.publisher_user_id == user.id

    # read-only field should not be set from input
    assert book.total_sales_to_date == 0

    # through table row created correctly
    through = AuthorBook.objects.get(book=book, author=a1)
    assert str(through.royalty_rate) == "0.1500"


def test_get_books_returns_only_authenticated_users_books(authed_client, user, other_user):
    a1 = make_author()

    make_book(publisher_user=user, isbn_13="9780000000001", title="Mine1", authors=[(a1, "0.10")])
    make_book(publisher_user=user, isbn_13="9780000000002", title="Mine2", authors=[(a1, "0.10")])
    make_book(publisher_user=other_user, isbn_13="9780000000003", title="NotMine", authors=[(a1, "0.10")])

    resp = authed_client.get("/api/books/")
    assert resp.status_code == 200, resp.content

    assert resp.data["count"] == 2
    titles = {r["title"] for r in resp.data["results"]}
    assert titles == {"Mine1", "Mine2"}


def test_get_books_pagination(authed_client, user):
    a1 = make_author()

    make_book(publisher_user=user, isbn_13="9780000000100", title="B0", authors=[(a1, "0.10")])
    make_book(publisher_user=user, isbn_13="9780000000101", title="B1", authors=[(a1, "0.10")])
    make_book(publisher_user=user, isbn_13="9780000000102", title="B2", authors=[(a1, "0.10")])

    resp1 = authed_client.get("/api/books/?page=1&page_size=2")
    assert resp1.status_code == 200
    assert resp1.data["count"] == 3
    assert len(resp1.data["results"]) == 2

    resp2 = authed_client.get("/api/books/?page=2&page_size=2")
    assert resp2.status_code == 200
    assert len(resp2.data["results"]) == 1


def test_get_books_fields_filtering(authed_client, user):
    a1 = make_author()
    make_book(publisher_user=user, isbn_13="9780000009999", title="B", authors=[(a1, "0.10")])

    resp = authed_client.get("/api/books/?fields=title,isbn_13")
    assert resp.status_code == 200
    item = resp.data["results"][0]

    assert set(item.keys()) == {"title", "isbn_13"}


def test_patch_updates_book(authed_client, user):
    a1 = make_author()
    b = make_book(publisher_user=user, isbn_13="9780000001234", title="Old", authors=[(a1, "0.10")])

    resp = authed_client.patch(f"/api/books/{b.id}/", {"title": "New"}, format="json")
    assert resp.status_code == 200, resp.content

    b.refresh_from_db()
    assert b.title == "New"


def test_delete_removes_book(authed_client, user):
    a1 = make_author()
    b = make_book(publisher_user=user, isbn_13="9780000005678", title="ToDelete", authors=[(a1, "0.10")])

    resp = authed_client.delete(f"/api/books/{b.id}/")
    assert resp.status_code == 204

    assert not Book.objects.filter(id=b.id).exists()


def test_patch_forbidden_on_someone_elses_book(authed_client, other_user):
    # authed_client is authenticated as "user" fixture, not other_user
    a1 = make_author()
    b = make_book(publisher_user=other_user, isbn_13="9780000007777", title="Other", authors=[(a1, "0.10")])

    resp = authed_client.patch(f"/api/books/{b.id}/", {"title": "Hack"}, format="json")
    # get_object_or_404 with publisher_user=request.user causes 404 (not 403)
    assert resp.status_code == 404


def test_post_duplicate_isbn_13_returns_400(authed_client):
    a1 = make_author()

    payload = {
        "title": "Dune",
        "publication_date": "1965-08-01",
        "isbn_13": "9780441172719",
        "isbn_10": "0441172717",
        "authors": [
            {"author_id": a1.id, "royalty_rate": "0.15"},
        ],
    }

    # First create should succeed
    resp1 = authed_client.post("/api/books/", payload, format="json")
    assert resp1.status_code == 201, resp1.content

    # Second create with same isbn_13 should fail due to unique constraint
    payload2 = {
        **payload,
        "title": "Another Title",  # change something else so only ISBN is the conflict
    }
    resp2 = authed_client.post("/api/books/", payload2, format="json")
    assert resp2.status_code == 400, resp2.content

    # DRF typically returns field-specific errors like {"isbn_13": ["..."]}
    assert "isbn_13" in resp2.data


def test_get_books_search(authed_client, user):
    a1 = make_author()
    # Create books
    make_book(publisher_user=user, isbn_13="9780000001000", title="Harry Potter", authors=[(a1, "0.10")])
    make_book(publisher_user=user, isbn_13="9780000002000", title="Lord of the Rings", authors=[(a1, "0.10")])
    make_book(publisher_user=user, isbn_13="9781234567890", title="Test Book", authors=[(a1, "0.10")])

    # Search by Title
    resp = authed_client.get("/api/books/?q=Harry")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["title"] == "Harry Potter"

    # Search by part of Title (case insensitive)
    resp = authed_client.get("/api/books/?q=rings")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["title"] == "Lord of the Rings"

    # Search by ISBN (exact)
    resp = authed_client.get("/api/books/?q=9781234567890")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["isbn_13"] == "9781234567890"

    # Search by ISBN (with dashes - should still find it)
    resp = authed_client.get("/api/books/?q=978-123-456-7890")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["isbn_13"] == "9781234567890"


def test_get_books_published_before_filter(authed_client, user):
    a1 = make_author()
    # Create books with specific publication dates
    make_book(publisher_user=user, isbn_13="9780000003001", title="Old Book", 
              authors=[(a1, "0.10")]) # Will defaults to 2000-01-01
    
    make_book(publisher_user=user, isbn_13="9780000003002", title="New Book", 
              authors=[(a1, "0.10")]) # Will defaults to 2000-01-01

    # Update dates manually
    b1 = Book.objects.get(isbn_13="9780000003001")
    b1.publication_date = "2020-01-01"
    b1.save()

    b2 = Book.objects.get(isbn_13="9780000003002")
    b2.publication_date = "2025-01-01"
    b2.save()

    # Filter: published_before=2022-01-01 (Should include 2020, exclude 2025)
    resp = authed_client.get("/api/books/?published_before=2022-01-01")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["title"] == "Old Book"

    # Filter: published_before=2025-01-01 (Should include 2025 too)
    resp = authed_client.get("/api/books/?published_before=2025-01-01")
    assert resp.status_code == 200
    assert resp.data["count"] == 2

