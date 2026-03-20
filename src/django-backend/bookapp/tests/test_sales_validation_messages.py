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
    author = Author.objects.create(name="Test Author", email="test@test.com")
    return Book.objects.create(
        title="Valid Book",
        publication_date="2020-01-01",
        isbn_13="9780000000123",
        author=author,
        cover_price="20.00",
        print_cost="10.00",
        distributor_author_royalty_rate="0.10",
        hand_sold_author_royalty_rate="0.20",
    )

def test_missing_quantity_message(authed_client, sample_book):
    payload = {
        "book": sample_book.id,
        "publisher_revenue": "100.00",
        "author_royalty": "10.00",
        "sale_source": "distributor",
        "distributor": "Ingram Spark",
        "date": "2023-01"
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 400
    # verify specifically for the custom error message
    assert resp.data["quantity"] == ["Quantity is required for print and ebook sales."]

def test_negative_quantity_message(authed_client, sample_book):
    payload = {
        "book": sample_book.id,
        "quantity": -5,
        "publisher_revenue": "100.00",
        "author_royalty": "10.00",
        "sale_source": "distributor",
        "distributor": "Ingram Spark",
        "date": "2023-01"
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 400
    assert resp.data["quantity"] == ["Quantity must be a positive integer."]

def test_missing_revenue_message(authed_client, sample_book):
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "sale_source": "distributor",
        "distributor": "Ingram Spark",
        # "publisher_revenue": "100.00", # Missing
        "date": "2023-01"
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 400
    assert resp.data["publisher_revenue"] == ["Publisher revenue is required for distributor sales."]

def test_missing_date_message(authed_client, sample_book):
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "publisher_revenue": "100.00",
        "author_royalty": "10.00",
        "sale_source": "distributor",
        "distributor": "Ingram Spark",
        # "date": "2023-01-01" # Missing
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 400
    assert resp.data["date"] == ["Date is required."]

def test_missing_sale_source_message(authed_client, sample_book):
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "publisher_revenue": "100.00",
        "author_royalty": "10.00",
        # "sale_source": missing
        "date": "2023-01"
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 400
    assert resp.data["sale_source"] == ["Sale source is required."]

def test_missing_author_royalty_message(authed_client, sample_book):
    """author_royalty is computed server-side (read_only), so omitting it should succeed."""
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "publisher_revenue": "100.00",
        "sale_source": "distributor",
        "distributor": "Ingram Spark",
        # "author_royalty": omitted — computed from publisher_revenue * rate
        "date": "2023-01"
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 201
    # Royalty is auto-calculated: 100.00 * 0.10 = 10.00
    assert resp.data["author_royalty"] == "10.00"

def test_null_value_message(authed_client, sample_book):
    # Test sending explicit null
    payload = {
        "book": sample_book.id,
        "quantity":  None,
        "publisher_revenue": None,
        "author_royalty": None,
        "sale_source": None,
        "date": None
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 400
    # sale_source=None fails ChoiceField validation (field-level)
    assert resp.data["sale_source"] == ["Sale source is required."]
    # date=None fails MonthYearField validation (field-level)
    assert resp.data["date"] == ["Date is required."]
    # quantity is allow_null=True, so null passes field-level validation;
    # the cross-field check in validate() never runs because sale_source fails first
    assert "quantity" not in resp.data
