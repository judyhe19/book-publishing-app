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
        released=True,
    )
    return book

def test_create_sale_negative_quantity(authed_client, sample_book):
    payload = {
        "book": sample_book.id,
        "quantity": -5,
        "publisher_revenue": "100.00",
        "sale_source": "distributor",
        "distributor": "Ingram Spark",
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
        "distributor": "Ingram Spark",
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
        "distributor": "Ingram Spark",
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
        "distributor": "Ingram Spark",
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
        "distributor": "Ingram Spark",
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
        "distributor": "Ingram Spark",
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
        "distributor": "Ingram Spark",
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
        "distributor": "Ingram Spark",
        "date": "0000-01"
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 400
    assert "date" in resp.data
    assert resp.data["date"][0] == "Cannot accept year 0."


# ---------------------------------------------------------------
# New cross-field validation tests
# ---------------------------------------------------------------

def test_distributor_required_for_distributor_sales(authed_client, sample_book):
    """Distributor must be specified when sale_source is 'distributor'."""
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "publisher_revenue": "100.00",
        "sale_source": "distributor",
        "date": "2023-01",
        # no distributor
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 400
    assert "distributor" in resp.data


def test_invalid_distributor_value(authed_client, sample_book):
    """Distributor must be one of the valid choices."""
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "publisher_revenue": "100.00",
        "sale_source": "distributor",
        "distributor": "Unknown Corp",
        "date": "2023-01",
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 400
    assert "distributor" in resp.data


def test_ingram_spark_only_allows_print(authed_client, sample_book):
    """Ingram Spark distributor must use 'print' format."""
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "publisher_revenue": "100.00",
        "sale_source": "distributor",
        "distributor": "Ingram Spark",
        "format": "ebook",
        "date": "2023-01",
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 400
    assert "format" in resp.data


def test_amazon_allows_all_formats(authed_client, sample_book):
    """Amazon distributor allows print, ebook, and kindle unlimited."""
    # print
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "publisher_revenue": "100.00",
        "sale_source": "distributor",
        "distributor": "Amazon",
        "format": "print",
        "date": "2023-01",
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 201

    # ebook
    payload["format"] = "ebook"
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 201

    # kindle unlimited (needs kenp, no quantity)
    payload["format"] = "kindle unlimited"
    payload["kenp"] = 500
    payload.pop("quantity")
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 201


def test_other_distributor_rejects_kindle_unlimited(authed_client, sample_book):
    """'Other' distributor only allows print and ebook, not kindle unlimited."""
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "publisher_revenue": "100.00",
        "sale_source": "distributor",
        "distributor": "Other",
        "format": "kindle unlimited",
        "kenp": 500,
        "date": "2023-01",
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 400
    assert "format" in resp.data


def test_handsold_must_be_print(authed_client, sample_book):
    """Handsold sales must use 'print' format."""
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "sale_source": "handsold",
        "format": "ebook",
        "date": "2023-01",
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 400
    assert "format" in resp.data


def test_handsold_currency_locked_to_usd(authed_client, sample_book):
    """Handsold sales must use USD currency."""
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "sale_source": "handsold",
        "currency": "GBP",
        "date": "2023-01",
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 400
    assert "currency" in resp.data


def test_handsold_valid_defaults_usd(authed_client, sample_book):
    """Handsold sales should default currency to USD and compute revenue."""
    payload = {
        "book": sample_book.id,
        "quantity": 5,
        "sale_source": "handsold",
        "date": "2023-01",
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 201
    assert resp.data["currency"] == "USD"
    # revenue = 5 * (20.00 - 10.00) = 50.00
    assert Decimal(resp.data["publisher_revenue"]) == Decimal("50.00")


def test_kindle_unlimited_requires_kenp(authed_client, sample_book):
    """Kindle Unlimited sales must provide KENP."""
    payload = {
        "book": sample_book.id,
        "publisher_revenue": "100.00",
        "sale_source": "distributor",
        "distributor": "Amazon",
        "format": "kindle unlimited",
        "date": "2023-01",
        # no kenp
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 400
    assert "kenp" in resp.data


def test_kindle_unlimited_rejects_quantity(authed_client, sample_book):
    """Kindle Unlimited sales must not have quantity."""
    payload = {
        "book": sample_book.id,
        "publisher_revenue": "100.00",
        "sale_source": "distributor",
        "distributor": "Amazon",
        "format": "kindle unlimited",
        "kenp": 500,
        "quantity": 10,
        "date": "2023-01",
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 400
    assert "quantity" in resp.data


# ---------------------------------------------------------------
# Kickstarter sale source validation tests
# ---------------------------------------------------------------

def test_kickstarter_allows_print(authed_client, sample_book):
    """Kickstarter sales can use 'print' format."""
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "sale_source": "kickstarter",
        "format": "print",
        "date": "2023-01",
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 201


def test_kickstarter_allows_ebook(authed_client, sample_book):
    """Kickstarter sales can use 'ebook' format."""
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "sale_source": "kickstarter",
        "format": "ebook",
        "date": "2023-01",
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 201


def test_kickstarter_rejects_kindle_unlimited(authed_client, sample_book):
    """Kickstarter sales cannot use 'kindle unlimited' format."""
    payload = {
        "book": sample_book.id,
        "sale_source": "kickstarter",
        "format": "kindle unlimited",
        "kenp": 500,
        "date": "2023-01",
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 400
    assert "format" in resp.data


def test_kickstarter_currency_locked_to_usd(authed_client, sample_book):
    """Kickstarter sales must use USD currency."""
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "sale_source": "kickstarter",
        "currency": "GBP",
        "date": "2023-01",
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 400
    assert "currency" in resp.data


def test_kickstarter_defaults_usd(authed_client, sample_book):
    """Kickstarter sales should default currency to USD."""
    payload = {
        "book": sample_book.id,
        "quantity": 5,
        "sale_source": "kickstarter",
        "date": "2023-01",
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 201
    assert resp.data["currency"] == "USD"


def test_kickstarter_computes_revenue(authed_client, sample_book):
    """Kickstarter revenue = (cover_price - print_cost) × quantity."""
    payload = {
        "book": sample_book.id,
        "quantity": 5,
        "sale_source": "kickstarter",
        "date": "2023-01",
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 201
    # sample_book: cover_price=20.00, print_cost=10.00
    # revenue = 5 * (20.00 - 10.00) = 50.00
    assert Decimal(resp.data["publisher_revenue"]) == Decimal("50.00")


def test_kickstarter_uses_handsold_royalty_rate(authed_client, sample_book):
    """Kickstarter royalty uses hand_sold_author_royalty_rate (0.20)."""
    payload = {
        "book": sample_book.id,
        "quantity": 5,
        "sale_source": "kickstarter",
        "date": "2023-01",
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 201
    # revenue = 50.00, royalty = 50.00 * 0.20 = 10.00
    assert Decimal(resp.data["author_royalty"]) == Decimal("10.00")


def test_kickstarter_distributor_cleared(authed_client, sample_book):
    """Distributor field is cleared for kickstarter sales even if sent."""
    payload = {
        "book": sample_book.id,
        "quantity": 10,
        "sale_source": "kickstarter",
        "distributor": "Amazon",
        "date": "2023-01",
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 201
    assert resp.data["distributor"] is None


def test_kickstarter_ignores_provided_revenue(authed_client, sample_book):
    """Kickstarter ignores client-sent publisher_revenue and computes it."""
    payload = {
        "book": sample_book.id,
        "quantity": 5,
        "sale_source": "kickstarter",
        "publisher_revenue": "999.99",  # should be ignored
        "date": "2023-01",
    }
    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 201
    # Should be computed: 5 * (20.00 - 10.00) = 50.00, not 999.99
    assert Decimal(resp.data["publisher_revenue"]) == Decimal("50.00")
