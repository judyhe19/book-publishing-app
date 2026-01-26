import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from bookapp.models import Book, Author

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


def make_book(*, publisher_user, isbn_13, title="T", author=None):
    book = Book.objects.create(
        title=title,
        publication_date="2000-01-01",
        isbn_13=isbn_13,
        isbn_10=None,
        author_royalty_rate="0.10",
        total_sales_to_date=0,
        publisher_user=publisher_user,
    )
    if author is not None:
        book.authors.add(author)
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
        "author_royalty_rate": "0.15",
        "total_sales_to_date": 999,  # should be ignored due to read_only_fields
        "authors": [a1.id],
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

    assert list(book.authors.values_list("id", flat=True)) == [a1.id]


def test_get_books_returns_only_authenticated_users_books(authed_client, user, other_user):
    a1 = make_author()

    make_book(publisher_user=user, isbn_13="9780000000001", title="Mine1", author=a1)
    make_book(publisher_user=user, isbn_13="9780000000002", title="Mine2", author=a1)
    make_book(publisher_user=other_user, isbn_13="9780000000003", title="NotMine", author=a1)

    resp = authed_client.get("/api/books/")
    assert resp.status_code == 200, resp.content

    assert resp.data["count"] == 2
    titles = {r["title"] for r in resp.data["results"]}
    assert titles == {"Mine1", "Mine2"}


def test_get_books_pagination(authed_client, user):
    a1 = make_author()

    make_book(publisher_user=user, isbn_13="9780000000100", title="B0", author=a1)
    make_book(publisher_user=user, isbn_13="9780000000101", title="B1", author=a1)
    make_book(publisher_user=user, isbn_13="9780000000102", title="B2", author=a1)

    resp1 = authed_client.get("/api/books/?page=1&page_size=2")
    assert resp1.status_code == 200
    assert resp1.data["count"] == 3
    assert len(resp1.data["results"]) == 2

    resp2 = authed_client.get("/api/books/?page=2&page_size=2")
    assert resp2.status_code == 200
    assert len(resp2.data["results"]) == 1


def test_get_books_fields_filtering(authed_client, user):
    a1 = make_author()
    make_book(publisher_user=user, isbn_13="9780000009999", title="B", author=a1)

    resp = authed_client.get("/api/books/?fields=title,isbn_13")
    assert resp.status_code == 200
    item = resp.data["results"][0]

    assert set(item.keys()) == {"title", "isbn_13"}


def test_patch_updates_book(authed_client, user):
    a1 = make_author()
    b = make_book(publisher_user=user, isbn_13="9780000001234", title="Old", author=a1)

    resp = authed_client.patch(f"/api/books/{b.id}/", {"title": "New"}, format="json")
    assert resp.status_code == 200, resp.content

    b.refresh_from_db()
    assert b.title == "New"


def test_delete_removes_book(authed_client, user):
    a1 = make_author()
    b = make_book(publisher_user=user, isbn_13="9780000005678", title="ToDelete", author=a1)

    resp = authed_client.delete(f"/api/books/{b.id}/")
    assert resp.status_code == 204

    assert not Book.objects.filter(id=b.id).exists()


def test_patch_forbidden_on_someone_elses_book(authed_client, other_user):
    # authed_client is authenticated as "user" fixture, not other_user
    # We'll create a book owned by other_user and ensure we can't edit it.
    a1 = make_author()
    b = make_book(publisher_user=other_user, isbn_13="9780000007777", title="Other", author=a1)

    resp = authed_client.patch(f"/api/books/{b.id}/", {"title": "Hack"}, format="json")
    # get_object_or_404 with publisher_user=request.user causes 404 (not 403)
    assert resp.status_code == 404

def test_post_duplicate_isbn_13_returns_400(authed_client, user):
    a1 = make_author()

    payload = {
        "title": "Dune",
        "publication_date": "1965-08-01",
        "isbn_13": "9780441172719",
        "isbn_10": "0441172717",
        "author_royalty_rate": "0.15",
        "authors": [a1.id],
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

    # DRF usually returns field-specific errors like {"isbn_13": ["..."]}
    assert "isbn_13" in resp2.data
