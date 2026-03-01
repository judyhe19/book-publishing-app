import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from decimal import Decimal
from bookapp.models import Book, Author, Sale

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
        author=author,
        distributor_author_royalty_rate=Decimal("0.10"),
        hand_sold_author_royalty_rate=Decimal("0.20"),
        cover_price=Decimal("20.00"),
        print_cost=Decimal("10.00"),
    )
    return book

def test_create_sale_negative_quantity(authed_client, sample_book):
    payload = {
        "book": sample_book.id,
        "quantity": -5,
        "publisher_revenue": "100.00",
        "sale_source": "distributor",
        "date": "2023-01"
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 400
    assert "quantity" in resp.data

def test_create_sale_zero_quantity(authed_client, sample_book):
    payload = {
        "book": sample_book.id,
        "quantity": 0,
        "publisher_revenue": "100.00",
        "sale_source": "distributor",
        "date": "2023-01"
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 400
    assert "quantity" in resp.data

def test_create_sale_negative_revenue(authed_client, sample_book):
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "publisher_revenue": "-50.00",
        "sale_source": "distributor",
        "date": "2023-01"
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 400
    assert "publisher_revenue" in resp.data

def test_create_sale_date_before_publication(authed_client, sample_book):
    # Book pub date is 2020-01-01
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "publisher_revenue": "100.00",
        "sale_source": "distributor",
        "date": "2019-12" # Before publication
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 400
    assert "date" in resp.data

def test_create_sale_invalid_source(authed_client, sample_book):
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "publisher_revenue": "100.00",
        "sale_source": "invalid",
        "date": "2023-01"
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 400
    assert "sale_source" in resp.data

def test_create_sale_valid(authed_client, sample_book):
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "publisher_revenue": "100.00",
        "sale_source": "distributor",
        "date": "2023-01"
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 201

def test_edit_sale_negative_quantity(authed_client, sample_book):
    # Create valid sale first
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "publisher_revenue": "100.00",
        "author_royalty": "10.00",
        "sale_source": "distributor",
        "date": "2023-01"
    }
    create_resp = authed_client.post("/api/sales/", payload, format="json")
    assert create_resp.status_code == 201
    sale_id = create_resp.data['id']
    
    # Try to edit with negative quantity
    edit_payload = {
        "quantity": -5
    }
    resp = authed_client.patch(f"/api/sales/{sale_id}/", edit_payload, format="json")
    assert resp.status_code == 400
    assert "quantity" in resp.data

def test_create_sale_year_zero_date(authed_client, sample_book):
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "publisher_revenue": "100.00",
        "sale_source": "distributor",
        "date": "0000-01"
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 400
    assert "date" in resp.data
    assert resp.data["date"][0] == "Cannot accept year 0."
