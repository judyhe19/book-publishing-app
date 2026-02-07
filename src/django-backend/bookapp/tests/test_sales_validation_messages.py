import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from bookapp.models import Book, Author

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
    return Book.objects.create(
        title="Valid Book",
        publication_date="2020-01-01",
        isbn_13="9780000000123",
    )

def test_missing_quantity_message(authed_client, sample_book):
    payload = {
        "book": sample_book.id,
        "publisher_revenue": "100.00",
        "date": "2023-01-01"
    }
    resp = authed_client.post("/api/sale/create", payload, format="json")
    assert resp.status_code == 400
    # verify specifically for the custom error message
    assert resp.data["quantity"] == ["Quantity is required."]

def test_negative_quantity_message(authed_client, sample_book):
    payload = {
        "book": sample_book.id,
        "quantity": -5,
        "publisher_revenue": "100.00",
        "date": "2023-01-01"
    }
    resp = authed_client.post("/api/sale/create", payload, format="json")
    assert resp.status_code == 400
    assert resp.data["quantity"] == ["Quantity must be a positive integer."]

def test_missing_revenue_message(authed_client, sample_book):
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        # "publisher_revenue": "100.00", # Missing
        "date": "2023-01-01"
    }
    resp = authed_client.post("/api/sale/create", payload, format="json")
    assert resp.status_code == 400
    assert resp.data["publisher_revenue"] == ["Publisher revenue is required."]

def test_missing_date_message(authed_client, sample_book):
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "publisher_revenue": "100.00",
        # "date": "2023-01-01" # Missing
    }
    resp = authed_client.post("/api/sale/create", payload, format="json")
    assert resp.status_code == 400
    assert resp.data["date"] == ["Date is required."]

def test_null_value_message(authed_client, sample_book):
    # Test sending explicit null
    payload = {
        "book": sample_book.id,
        "quantity":  None,
        "publisher_revenue": None,
        "date": None
    }
    resp = authed_client.post("/api/sale/create", payload, format="json")
    assert resp.status_code == 400
    assert resp.data["quantity"] == ["Quantity is required."]
    assert resp.data["publisher_revenue"] == ["Publisher revenue is required."]
    assert resp.data["date"] == ["Date is required."]
