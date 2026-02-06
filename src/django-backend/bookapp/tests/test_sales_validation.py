import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from decimal import Decimal
from bookapp.models import Book, Author, Sale, AuthorSale

pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user():
    return User.objects.create_user(username="u1", password="pass12345")

@pytest.fixture
def authed_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client

@pytest.fixture
def sample_book(user):
    author = Author.objects.create(name="Test Author")
    book = Book.objects.create(
        title="Valid Book",
        publication_date="2020-01-01",
        isbn_13="9780000000123",
    )
    return book

def test_create_sale_negative_quantity(authed_client, sample_book):
    payload = {
        "book": sample_book.id,
        "quantity": -5,
        "publisher_revenue": "100.00",
        "date": "2023-01-01"
    }
    resp = authed_client.post("/api/sale/create", payload, format="json")
    assert resp.status_code == 400
    assert "quantity" in resp.data

def test_create_sale_zero_quantity(authed_client, sample_book):
    payload = {
        "book": sample_book.id,
        "quantity": 0,
        "publisher_revenue": "100.00",
        "date": "2023-01-01"
    }
    resp = authed_client.post("/api/sale/create", payload, format="json")
    assert resp.status_code == 400
    assert "quantity" in resp.data

def test_create_sale_negative_revenue(authed_client, sample_book):
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "publisher_revenue": "-50.00",
        "date": "2023-01-01"
    }
    resp = authed_client.post("/api/sale/create", payload, format="json")
    assert resp.status_code == 400
    assert "publisher_revenue" in resp.data

def test_create_sale_negative_royalties(authed_client, sample_book):
    # Need to know author ID (but we didn't attach author in fixture explicitly via AuthorBook... 
    # wait, book.authors needs AuthorBook potentially, or just use the ID even if not linked?
    # The serializer iterates specifically over what's passed in author_royalties check)
    a1 = Author.objects.first()
    
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "publisher_revenue": "100.00",
        "date": "2023-01-01",
        "author_royalties": {
            str(a1.id): "-10.00"
        }
    }
    resp = authed_client.post("/api/sale/create", payload, format="json")
    assert resp.status_code == 400
    assert "author_royalties" in resp.data

def test_create_sale_date_before_publication(authed_client, sample_book):
    # Book pub date is 2020-01-01
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "publisher_revenue": "100.00",
        "date": "2019-12-31" # Before publication
    }
    resp = authed_client.post("/api/sale/create", payload, format="json")
    assert resp.status_code == 400
    assert "date" in resp.data

def test_create_sale_valid(authed_client, sample_book):
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "publisher_revenue": "100.00",
        "date": "2023-01-01"
    }
    resp = authed_client.post("/api/sale/create", payload, format="json")
    assert resp.status_code == 201

def test_edit_sale_negative_quantity(authed_client, sample_book):
    # Create valid sale first
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "publisher_revenue": "100.00",
        "date": "2023-01-01"
    }
    create_resp = authed_client.post("/api/sale/create", payload, format="json")
    assert create_resp.status_code == 201
    sale_id = create_resp.data['id']
    
    # Try to edit with negative quantity
    edit_payload = {
        "quantity": -5
    }
    resp = authed_client.post(f"/api/sale/{sale_id}/edit", edit_payload, format="json")
    assert resp.status_code == 400
    assert "quantity" in resp.data


