import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
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

import uuid

def make_author(name="Frank Herbert"):
    email = f"{name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:6]}@test.com"
    return Author.objects.create(name=name, email=email)

def make_book(*, isbn_13, title="T", author=None, royalty_rate="0.10", cover_price="20.00", print_cost="10.00"):
    book = Book.objects.create(
        title=title,
        publication_date="2000-01-01",
        isbn_13=isbn_13,
        isbn_10=None,
        author=author,
        distributor_author_royalty_rate=Decimal(royalty_rate),
        hand_sold_author_royalty_rate=Decimal("0.20"),
        cover_price=Decimal(cover_price),
        print_cost=Decimal(print_cost),
        released=True,
    )
    return book

def test_create_sale(authed_client, user):
    a1 = make_author()
    b1 = make_book(isbn_13="9780000000001", author=a1, royalty_rate="0.10")

    payload = {
        "book": b1.id,
        "quantity": 100,
        "publisher_revenue": "1000.00",
        "sale_source": "distributor",
        "distributor": "Ingram Spark",
        "date": "2023-01"
    }

    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 201, resp.content

    assert Sale.objects.count() == 1
    sale = Sale.objects.first()
    assert sale.quantity == 100
    assert sale.publisher_revenue == Decimal("1000.00")
    assert sale.author_royalty == Decimal("100.00")
    assert sale.sale_source == "distributor"
    assert sale.author_paid is False

def test_create_sale_handsold(authed_client, user):
    a1 = make_author()
    b1 = make_book(isbn_13="9780000000002", author=a1, royalty_rate="0.10", cover_price="20.00", print_cost="10.00")

    payload = {
        "book": b1.id,
        "quantity": 50,
        "sale_source": "handsold",
        "date": "2023-01",
    }

    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 201, resp.content

    sale = Sale.objects.first()
    assert sale.sale_source == "handsold"
    # Handsold revenue is 50 * (20 - 10) = 500
    assert sale.publisher_revenue == Decimal("500.00")
    # Royalty is 500 * handsold diff rate (0.20) = 100
    assert sale.author_royalty == Decimal("100.00")

def test_create_many_sales(authed_client, user):
    a1 = make_author()
    b1 = make_book(isbn_13="9780000000003", author=a1)

    payload = [
        {
            "book": b1.id,
            "quantity": 10,
            "publisher_revenue": "100.00",
            "sale_source": "distributor",
            "distributor": "Ingram Spark",
            "date": "2023-01"
        },
        {
            "book": b1.id,
            "quantity": 20,
            "publisher_revenue": "200.00",
            "sale_source": "distributor",
            "distributor": "Ingram Spark",
            "date": "2023-02"
        }
    ]

    resp = authed_client.post("/api/sales/create-many/", payload, format="json")
    assert resp.status_code == 201, resp.content
    
    assert Sale.objects.count() == 2

def test_get_all_sales_filtering(authed_client, user):
    a1 = make_author()
    b1 = make_book(isbn_13="9780000000004", title="Book1", author=a1)
    
    b2 = make_book(isbn_13="9780000000005", title="Book2", author=a1)

    # Sale for Book 1
    Sale.objects.create(
        book=b1, quantity=10, publisher_revenue=100,
        author_royalty=10, sale_source="distributor", date="2023-01-01"
    )
    # Sale for Book 2
    Sale.objects.create(
        book=b2, quantity=10, publisher_revenue=100,
        author_royalty=10, sale_source="distributor", date="2023-01-01"
    )

    # Test Filter by Book
    resp = authed_client.get(f"/api/sales/?book_id={b1.id}")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["book"] == b1.id


def test_edit_sale_updates_fields(authed_client, user):
    a1 = make_author()
    b1 = make_book(isbn_13="9780000000006", author=a1, royalty_rate="0.10")
    
    sale = Sale.objects.create(
        book=b1, quantity=10, publisher_revenue=Decimal("100.00"),
        author_royalty=Decimal("10.00"), sale_source="distributor",
        distributor="Ingram Spark", date="2023-01-01"
    )
    
    payload = {
        "quantity": 20,
        "publisher_revenue": "200.00",
    }
    
    resp = authed_client.patch(f"/api/sales/{sale.id}/", payload, format="json")
    assert resp.status_code == 200
    
    sale.refresh_from_db()
    assert sale.quantity == 20
    assert sale.publisher_revenue == Decimal("200.00")
    # Should recompute royalty: 200 * 0.10 = 20.00
    assert sale.author_royalty == Decimal("20.00")

def test_edit_sale_updates_author_paid(authed_client, user):
    a1 = make_author()
    b1 = make_book(isbn_13="9780000000008", author=a1, royalty_rate="0.10")
    
    sale = Sale.objects.create(
        book=b1, quantity=10, publisher_revenue=Decimal("100.00"),
        author_royalty=Decimal("10.00"), sale_source="distributor",
        distributor="Ingram Spark", date="2023-01-01"
    )
    
    assert sale.author_paid is False
    
    # Update to set author_paid = True
    payload = {"author_paid": True}
    
    resp = authed_client.patch(f"/api/sales/{sale.id}/", payload, format="json")
    assert resp.status_code == 200
    
    sale.refresh_from_db()
    assert sale.author_paid is True
    
    # Update back to False
    payload2 = {"author_paid": False}
    resp2 = authed_client.patch(f"/api/sales/{sale.id}/", payload2, format="json")
    assert resp2.status_code == 200
    
    sale.refresh_from_db()
    assert sale.author_paid is False

def test_delete_sale(authed_client, user):
    a1 = make_author()
    b1 = make_book(isbn_13="9780000000007", author=a1)
    sale = Sale.objects.create(
        book=b1, quantity=10, publisher_revenue=100,
        author_royalty=10, sale_source="distributor", date="2023-01-01"
    )
    
    resp = authed_client.delete(f"/api/sales/{sale.id}/")
    assert resp.status_code == 204
    
    assert Sale.objects.count() == 0


def test_get_sale_by_id(authed_client, user):
    """Test retrieving a single sale by its ID."""
    a1 = make_author(name="Test Author")
    b1 = make_book(isbn_13="9780000000023", title="Test Book", author=a1, royalty_rate="0.10")
    
    sale = Sale.objects.create(
        book=b1, quantity=15, publisher_revenue=Decimal("150.00"),
        author_royalty=Decimal("15.00"), sale_source="distributor", date="2023-05-01"
    )
    
    resp = authed_client.get(f"/api/sales/{sale.id}/")
    assert resp.status_code == 200
    
    data = resp.data
    assert data['id'] == sale.id
    assert data['book'] == b1.id
    assert data['quantity'] == 15
    assert Decimal(data['publisher_revenue']) == Decimal("150.00")
    assert Decimal(data['author_royalty']) == Decimal("15.00")
    assert data['sale_source'] == "distributor"
    assert data['author_paid'] is False
    assert data['date'] == "2023-05"


def test_get_sale_by_id_not_found(authed_client, user):
    """Test that requesting a non-existent sale returns 404."""
    resp = authed_client.get("/api/sales/99999/")
    assert resp.status_code == 404

def test_get_all_sales_sorting_and_date_filtering(authed_client, user):
    a1 = make_author(name="Alice")
    b1 = make_book(isbn_13="9780000000009", title="BookSort", author=a1)

    # Create sales with different dates and quantities
    s1 = Sale.objects.create(
        book=b1, quantity=10, publisher_revenue=100,
        author_royalty=10, sale_source="distributor", date="2023-01-01"
    )
    s2 = Sale.objects.create(
        book=b1, quantity=5, publisher_revenue=50,
        author_royalty=5, sale_source="distributor", date="2023-02-01"
    )
    s3 = Sale.objects.create(
        book=b1, quantity=20, publisher_revenue=200,
        author_royalty=20, sale_source="distributor", date="2023-03-01"
    )

    # 1. Test Date Range Filtering
    resp = authed_client.get(f"/api/sales/?start_date=2023-02-15&end_date=2023-02-15")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["id"] == s2.id

    # 2. Test default sort (date desc)
    resp = authed_client.get(f"/api/sales/")
    assert resp.status_code == 200
    assert resp.data["results"][0]["id"] == s3.id
    assert resp.data["results"][1]["id"] == s2.id
    assert resp.data["results"][2]["id"] == s1.id

    # 3. Verify response structure
    sale_data = resp.data["results"][0]
    assert 'sale_source' in sale_data
    assert 'author_royalty' in sale_data
    assert 'author_paid' in sale_data


def test_get_all_sales_ordering_by_date(authed_client, user):
    """Test server-side ordering by date (ascending and descending)."""
    a1 = make_author(name="TestAuthor")
    b1 = make_book(isbn_13="9780000000010", title="OrderBook", author=a1)

    s1 = Sale.objects.create(
        book=b1, quantity=10, publisher_revenue=100,
        author_royalty=10, sale_source="distributor", date="2023-01-01"
    )
    s2 = Sale.objects.create(
        book=b1, quantity=5, publisher_revenue=50,
        author_royalty=5, sale_source="distributor", date="2023-02-01"
    )
    s3 = Sale.objects.create(
        book=b1, quantity=20, publisher_revenue=200,
        author_royalty=20, sale_source="distributor", date="2023-03-01"
    )

    # Default ordering (should be -date, descending)
    resp = authed_client.get("/api/sales/")
    assert resp.status_code == 200
    assert [s['id'] for s in resp.data["results"]] == [s3.id, s2.id, s1.id]

    # Explicit descending date
    resp = authed_client.get("/api/sales/?ordering=-date")
    assert resp.status_code == 200
    assert [s['id'] for s in resp.data["results"]] == [s3.id, s2.id, s1.id]

    # Ascending date
    resp = authed_client.get("/api/sales/?ordering=date")
    assert resp.status_code == 200
    assert [s['id'] for s in resp.data["results"]] == [s1.id, s2.id, s3.id]


def test_get_all_sales_ordering_by_quantity(authed_client, user):
    """Test server-side ordering by quantity."""
    a1 = make_author(name="TestAuthor2")
    b1 = make_book(isbn_13="9780000000011", title="QtyBook", author=a1)

    s1 = Sale.objects.create(
        book=b1, quantity=10, publisher_revenue=100,
        author_royalty=10, sale_source="distributor", date="2023-01-01"
    )
    s2 = Sale.objects.create(
        book=b1, quantity=5, publisher_revenue=50,
        author_royalty=5, sale_source="distributor", date="2023-02-01"
    )
    s3 = Sale.objects.create(
        book=b1, quantity=20, publisher_revenue=200,
        author_royalty=20, sale_source="distributor", date="2023-03-01"
    )

    # Ascending quantity: 5, 10, 20
    resp = authed_client.get("/api/sales/?ordering=quantity")
    assert resp.status_code == 200
    assert [s['id'] for s in resp.data["results"]] == [s2.id, s1.id, s3.id]

    # Descending quantity: 20, 10, 5
    resp = authed_client.get("/api/sales/?ordering=-quantity")
    assert resp.status_code == 200
    assert [s['id'] for s in resp.data["results"]] == [s3.id, s1.id, s2.id]


def test_get_all_sales_ordering_by_publisher_revenue(authed_client, user):
    """Test server-side ordering by publisher_revenue."""
    a1 = make_author(name="TestAuthor3")
    b1 = make_book(isbn_13="9780000000012", title="RevBook", author=a1)

    s1 = Sale.objects.create(
        book=b1, quantity=10, publisher_revenue=100,
        author_royalty=10, sale_source="distributor", date="2023-01-01"
    )
    s2 = Sale.objects.create(
        book=b1, quantity=5, publisher_revenue=50,
        author_royalty=5, sale_source="distributor", date="2023-02-01"
    )
    s3 = Sale.objects.create(
        book=b1, quantity=20, publisher_revenue=200,
        author_royalty=20, sale_source="distributor", date="2023-03-01"
    )

    # Ascending revenue: 50, 100, 200
    resp = authed_client.get("/api/sales/?ordering=publisher_revenue")
    assert resp.status_code == 200
    assert [s['id'] for s in resp.data["results"]] == [s2.id, s1.id, s3.id]

    # Descending revenue: 200, 100, 50
    resp = authed_client.get("/api/sales/?ordering=-publisher_revenue")
    assert resp.status_code == 200
    assert [s['id'] for s in resp.data["results"]] == [s3.id, s1.id, s2.id]


def test_get_all_sales_ordering_by_book_title(authed_client, user):
    """Test server-side ordering by book_title."""
    a1 = make_author(name="TestAuthor4")
    b1 = make_book(isbn_13="9780000000013", title="Alpha Book", author=a1)
    b2 = make_book(isbn_13="9780000000014", title="Zeta Book", author=a1)
    b3 = make_book(isbn_13="9780000000015", title="Beta Book", author=a1)

    s1 = Sale.objects.create(
        book=b1, quantity=10, publisher_revenue=100,
        author_royalty=10, sale_source="distributor", date="2023-01-01"
    )
    s2 = Sale.objects.create(
        book=b2, quantity=5, publisher_revenue=50,
        author_royalty=5, sale_source="distributor", date="2023-02-01"
    )
    s3 = Sale.objects.create(
        book=b3, quantity=20, publisher_revenue=200,
        author_royalty=20, sale_source="distributor", date="2023-03-01"
    )

    # Ascending book_title: Alpha, Beta, Zeta
    resp = authed_client.get("/api/sales/?ordering=book_title")
    assert resp.status_code == 200
    assert [s['id'] for s in resp.data["results"]] == [s1.id, s3.id, s2.id]

    # Descending book_title: Zeta, Beta, Alpha
    resp = authed_client.get("/api/sales/?ordering=-book_title")
    assert resp.status_code == 200
    assert [s['id'] for s in resp.data["results"]] == [s2.id, s3.id, s1.id]


def test_get_all_sales_ordering_invalid_field_falls_back_to_date(authed_client, user):
    """Test that invalid ordering field falls back to default (-date)."""
    a1 = make_author(name="TestAuthor5")
    b1 = make_book(isbn_13="9780000000016", title="FallbackBook", author=a1)

    s1 = Sale.objects.create(
        book=b1, quantity=10, publisher_revenue=100,
        author_royalty=10, sale_source="distributor", date="2023-01-01"
    )
    s2 = Sale.objects.create(
        book=b1, quantity=5, publisher_revenue=50,
        author_royalty=5, sale_source="distributor", date="2023-02-01"
    )
    s3 = Sale.objects.create(
        book=b1, quantity=20, publisher_revenue=200,
        author_royalty=20, sale_source="distributor", date="2023-03-01"
    )

    # Invalid field should fallback to -date (descending)
    resp = authed_client.get("/api/sales/?ordering=invalid_field")
    assert resp.status_code == 200
    assert [s['id'] for s in resp.data["results"]] == [s3.id, s2.id, s1.id]

    resp = authed_client.get("/api/sales/?ordering=-bogus")
    assert resp.status_code == 200
    assert [s['id'] for s in resp.data["results"]] == [s3.id, s2.id, s1.id]


def test_get_all_sales_ordering_by_total_royalties(authed_client, user):
    """Test server-side ordering by author_royalty."""
    a1 = make_author(name="TestAuthor6")
    b1 = make_book(isbn_13="9780000000017", title="LowRoyalty", author=a1, royalty_rate="0.05")
    b2 = make_book(isbn_13="9780000000018", title="HighRoyalty", author=a1, royalty_rate="0.30")
    b3 = make_book(isbn_13="9780000000019", title="MedRoyalty", author=a1, royalty_rate="0.15")

    # s1: 5.00 royalties
    s1 = Sale.objects.create(
        book=b1, quantity=10, publisher_revenue=100,
        author_royalty=Decimal("5.00"), sale_source="distributor", date="2023-01-01"
    )
    # s2: 30.00 royalties
    s2 = Sale.objects.create(
        book=b2, quantity=10, publisher_revenue=100,
        author_royalty=Decimal("30.00"), sale_source="distributor", date="2023-02-01"
    )
    # s3: 15.00 royalties
    s3 = Sale.objects.create(
        book=b3, quantity=10, publisher_revenue=100,
        author_royalty=Decimal("15.00"), sale_source="distributor", date="2023-03-01"
    )

    # Ascending author_royalty: 5, 15, 30
    resp = authed_client.get("/api/sales/?ordering=author_royalty")
    assert resp.status_code == 200
    assert [s['id'] for s in resp.data["results"]] == [s1.id, s3.id, s2.id]

    # Descending author_royalty: 30, 15, 5
    resp = authed_client.get("/api/sales/?ordering=-author_royalty")
    assert resp.status_code == 200
    assert [s['id'] for s in resp.data["results"]] == [s2.id, s3.id, s1.id]


def test_get_all_sales_ordering_by_paid_status(authed_client, user):
    """Test server-side ordering by paid_status (author_paid boolean)."""
    a1 = make_author(name="TestAuthor7")
    b1 = make_book(isbn_13="9780000000020", title="PaidBook", author=a1)
    b2 = make_book(isbn_13="9780000000021", title="UnpaidBook", author=a1)
    b3 = make_book(isbn_13="9780000000022", title="PartialBook", author=a1)

    # s1: Paid
    s1 = Sale.objects.create(
        book=b1, quantity=10, publisher_revenue=100,
        author_royalty=10, sale_source="distributor", date="2023-01-01",
        author_paid=True,
    )
    
    # s2: Not paid
    s2 = Sale.objects.create(
        book=b2, quantity=10, publisher_revenue=100,
        author_royalty=10, sale_source="distributor", date="2023-02-01",
        author_paid=False,
    )
    
    # s3: Not paid
    s3 = Sale.objects.create(
        book=b3, quantity=10, publisher_revenue=100,
        author_royalty=10, sale_source="distributor", date="2023-03-01",
        author_paid=False,
    )

    # Ascending paid_status (False=0 first, True=1 last)
    resp = authed_client.get("/api/sales/?ordering=paid_status")
    assert resp.status_code == 200
    # Unpaid (False) should come first
    assert resp.data["results"][-1]['id'] == s1.id  # paid=True is last

    # Descending paid_status (True=1 first, False=0 last)
    resp = authed_client.get("/api/sales/?ordering=-paid_status")
    assert resp.status_code == 200
    assert resp.data["results"][0]['id'] == s1.id  # paid=True is first


def test_filter_by_author_name(authed_client, user):
    """Test filtering sales by author name (case-insensitive partial match)."""
    a1 = make_author(name="Alice Smith")
    a2 = make_author(name="Bob Jones")
    b1 = make_book(isbn_13="9780000000030", title="Book A", author=a1)
    b2 = make_book(isbn_13="9780000000031", title="Book B", author=a2)

    s1 = Sale.objects.create(
        book=b1, quantity=10, publisher_revenue=100,
        author_royalty=10, sale_source="distributor", date="2023-01-01"
    )
    s2 = Sale.objects.create(
        book=b2, quantity=20, publisher_revenue=200,
        author_royalty=20, sale_source="distributor", date="2023-02-01"
    )

    # Filter by "alice" (case-insensitive)
    resp = authed_client.get("/api/sales/?author_name=alice")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["id"] == s1.id

    # Filter by "jones"
    resp = authed_client.get("/api/sales/?author_name=jones")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["id"] == s2.id

    # No match
    resp = authed_client.get("/api/sales/?author_name=zzzzz")
    assert resp.status_code == 200
    assert resp.data["count"] == 0


def test_filter_by_sale_source(authed_client, user):
    """Test filtering sales by sale_source."""
    a1 = make_author(name="Charlie")
    b1 = make_book(isbn_13="9780000000032", title="Source Book", author=a1)

    s1 = Sale.objects.create(
        book=b1, quantity=10, publisher_revenue=100,
        author_royalty=10, sale_source="distributor", date="2023-01-01"
    )
    s2 = Sale.objects.create(
        book=b1, quantity=20, publisher_revenue=200,
        author_royalty=20, sale_source="handsold", date="2023-02-01"
    )

    # Filter distributor only
    resp = authed_client.get("/api/sales/?sale_source=distributor")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["id"] == s1.id

    # Filter handsold only
    resp = authed_client.get("/api/sales/?sale_source=handsold")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["id"] == s2.id

    # No filter returns both
    resp = authed_client.get("/api/sales/")
    assert resp.status_code == 200
    assert resp.data["count"] == 2


def test_filter_by_distributor(authed_client, user):
    """Test filtering sales by distributor."""
    a1 = make_author(name="Diana")
    b1 = make_book(isbn_13="9780000000040", title="Dist Book", author=a1)

    s1 = Sale.objects.create(
        book=b1, quantity=10, publisher_revenue=100,
        author_royalty=10, sale_source="distributor",
        distributor="Ingram Spark", date="2023-01-01"
    )
    s2 = Sale.objects.create(
        book=b1, quantity=20, publisher_revenue=200,
        author_royalty=20, sale_source="distributor",
        distributor="Amazon", date="2023-02-01"
    )
    s3 = Sale.objects.create(
        book=b1, quantity=5, publisher_revenue=50,
        author_royalty=5, sale_source="handsold",
        distributor=None, date="2023-03-01"
    )

    # Filter by Ingram Spark
    resp = authed_client.get("/api/sales/?distributor=Ingram Spark")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["id"] == s1.id

    # Filter by Amazon
    resp = authed_client.get("/api/sales/?distributor=Amazon")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["id"] == s2.id

    # No filter returns all
    resp = authed_client.get("/api/sales/")
    assert resp.status_code == 200
    assert resp.data["count"] == 3


def test_filter_by_format(authed_client, user):
    """Test filtering sales by format."""
    a1 = make_author(name="Eve")
    b1 = make_book(isbn_13="9780000000041", title="Format Book", author=a1)

    s1 = Sale.objects.create(
        book=b1, quantity=10, publisher_revenue=100,
        author_royalty=10, sale_source="distributor",
        distributor="Amazon", format="print", date="2023-01-01"
    )
    s2 = Sale.objects.create(
        book=b1, quantity=20, publisher_revenue=200,
        author_royalty=20, sale_source="distributor",
        distributor="Amazon", format="ebook", date="2023-02-01"
    )
    s3 = Sale.objects.create(
        book=b1, quantity=0, publisher_revenue=50,
        author_royalty=5, sale_source="distributor",
        distributor="Amazon", format="kindle unlimited",
        kenp=1500, date="2023-03-01"
    )

    # Filter by print
    resp = authed_client.get("/api/sales/?sale_format=print")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["id"] == s1.id

    # Filter by ebook
    resp = authed_client.get("/api/sales/?sale_format=ebook")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["id"] == s2.id

    # Filter by kindle unlimited
    resp = authed_client.get("/api/sales/?sale_format=kindle unlimited")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["id"] == s3.id

    # No filter returns all
    resp = authed_client.get("/api/sales/")
    assert resp.status_code == 200
    assert resp.data["count"] == 3


# ======================================================================
# CSV Export Tests
# ======================================================================

import csv
import io

def test_export_csv_basic(authed_client, user):
    """Test basic CSV export with BOM, headers, and correct values."""
    a1 = make_author(name="CSV Author")
    b1 = make_book(isbn_13="9780000000050", title="CSV Book", author=a1, royalty_rate="0.10")

    Sale.objects.create(
        book=b1, quantity=10, publisher_revenue=Decimal("100.00"),
        publisher_revenue_original=Decimal("100.00"),
        author_royalty=Decimal("10.00"), sale_source="distributor",
        distributor="Ingram Spark", format="print",
        currency="USD", date="2023-06-01", comment="test comment"
    )

    resp = authed_client.get("/api/sales/export-csv/")
    assert resp.status_code == 200
    assert resp["Content-Type"] == "text/csv; charset=utf-8"
    assert "hp-sales-export-" in resp["Content-Disposition"]
    assert resp["Content-Disposition"].endswith('.csv"')

    content = resp.content.decode("utf-8-sig")  # strips BOM
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)

    # Header row
    assert rows[0] == [
        "Date", "Title", "Author", "Source", "Distributor",
        "Format", "Quantity", "KENP", "Original Currency",
        "Pub. Revenue (Original)", "Pub. Revenue (USD)",
        "Author Royalty (USD)", "Royalty Status", "isProjected?", "Comment",
    ]

    # Data row
    assert len(rows) == 2
    row = rows[1]
    assert row[0] == "2023-06"
    assert row[1] == "CSV Book"
    assert row[2] == "CSV Author"
    assert row[3] == "Distributor"
    assert row[4] == "Ingram Spark"
    assert row[5] == "Print"
    assert row[6] == "10"
    assert row[7] == "N/A"
    assert row[8] == "USD"
    assert row[9] == "100.00"
    assert row[10] == "100.00"
    assert row[11] == "10.00"
    assert row[12] == "Unpaid"
    assert row[13] == "False"         # isProjected? — book is released by default
    assert row[14] == "test comment"


def test_export_csv_with_filters(authed_client, user):
    """Test that CSV export respects filters (only matching records)."""
    a1 = make_author(name="Filter Author")
    b1 = make_book(isbn_13="9780000000051", title="Filter Book", author=a1)

    Sale.objects.create(
        book=b1, quantity=5, publisher_revenue=Decimal("50.00"),
        publisher_revenue_original=Decimal("50.00"),
        author_royalty=Decimal("5.00"), sale_source="distributor",
        distributor="Amazon", format="print",
        currency="USD", date="2023-01-01"
    )
    Sale.objects.create(
        book=b1, quantity=10, publisher_revenue=Decimal("100.00"),
        publisher_revenue_original=Decimal("100.00"),
        author_royalty=Decimal("10.00"), sale_source="distributor",
        distributor="Amazon", format="print",
        currency="USD", date="2023-06-01"
    )

    resp = authed_client.get("/api/sales/export-csv/?start_date=2023-05&end_date=2023-07")
    content = resp.content.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(content)))

    assert len(rows) == 2  # header + 1 matching row
    assert rows[1][0] == "2023-06"


def test_export_csv_handsold_na_fields(authed_client, user):
    """Test that handsold records show N/A for Distributor and Print for Format."""
    a1 = make_author(name="Hand Author")
    b1 = make_book(isbn_13="9780000000052", title="Hand Book", author=a1,
                   cover_price="20.00", print_cost="10.00")

    Sale.objects.create(
        book=b1, quantity=5, publisher_revenue=Decimal("50.00"),
        publisher_revenue_original=Decimal("50.00"),
        author_royalty=Decimal("10.00"), sale_source="handsold",
        distributor=None, format="print",
        currency="USD", date="2023-03-01"
    )

    resp = authed_client.get("/api/sales/export-csv/")
    content = resp.content.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(content)))

    row = rows[1]
    assert row[3] == "Handsold"
    assert row[4] == "N/A"  # distributor
    assert row[5] == "Print"


def test_export_csv_kindle_unlimited(authed_client, user):
    """Test that Kindle Unlimited records show N/A for Quantity and correct KENP."""
    a1 = make_author(name="KU Author")
    b1 = make_book(isbn_13="9780000000053", title="KU Book", author=a1)

    Sale.objects.create(
        book=b1, quantity=None, publisher_revenue=Decimal("30.00"),
        publisher_revenue_original=Decimal("30.00"),
        author_royalty=Decimal("3.00"), sale_source="distributor",
        distributor="Amazon", format="kindle unlimited",
        kenp=1500, currency="USD", date="2023-04-01"
    )

    resp = authed_client.get("/api/sales/export-csv/")
    content = resp.content.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(content)))

    row = rows[1]
    assert row[5] == "Kindle Unlimited"
    assert row[6] == "N/A"  # quantity
    assert row[7] == "1500"  # KENP


# ======================================================================
# Kickstarter Sale Tests
# ======================================================================

def test_create_sale_kickstarter(authed_client, user):
    """Test creating a Kickstarter sale computes revenue and royalty correctly."""
    a1 = make_author(name="KS Author")
    b1 = make_book(isbn_13="9780000000060", author=a1, royalty_rate="0.10",
                   cover_price="20.00", print_cost="10.00")

    payload = {
        "book": b1.id,
        "quantity": 50,
        "sale_source": "kickstarter",
        "date": "2023-01",
    }

    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 201, resp.content

    sale = Sale.objects.get(id=resp.data["id"])
    assert sale.sale_source == "kickstarter"
    # Kickstarter revenue is 50 * (20.00 - 10.00) = 500.00
    assert sale.publisher_revenue == Decimal("500.00")
    # Kickstarter uses hand_sold_author_royalty_rate (0.20)
    assert sale.author_royalty == Decimal("100.00")
    assert sale.currency == "USD"
    assert sale.distributor is None


def test_create_sale_kickstarter_ebook(authed_client, user):
    """Test creating a Kickstarter ebook sale."""
    a1 = make_author(name="KS eBook Author")
    b1 = make_book(isbn_13="9780000000061", author=a1, cover_price="15.00", print_cost="5.00")

    payload = {
        "book": b1.id,
        "quantity": 20,
        "sale_source": "kickstarter",
        "format": "ebook",
        "date": "2023-06",
    }

    resp = authed_client.post("/api/sales/", payload, format="json")
    assert resp.status_code == 201, resp.content

    sale = Sale.objects.get(id=resp.data["id"])
    assert sale.format == "ebook"
    assert sale.sale_source == "kickstarter"
    # revenue = 20 * (15.00 - 5.00) = 200.00
    assert sale.publisher_revenue == Decimal("200.00")


def test_filter_by_kickstarter_source(authed_client, user):
    """Test filtering sales by kickstarter sale_source."""
    a1 = make_author(name="Filter KS")
    b1 = make_book(isbn_13="9780000000062", title="KS Filter Book", author=a1)

    Sale.objects.create(
        book=b1, quantity=10, publisher_revenue=100,
        author_royalty=10, sale_source="distributor",
        distributor="Ingram Spark", date="2023-01-01"
    )
    s2 = Sale.objects.create(
        book=b1, quantity=20, publisher_revenue=200,
        author_royalty=40, sale_source="kickstarter",
        date="2023-02-01"
    )

    resp = authed_client.get("/api/sales/?sale_source=kickstarter")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["id"] == s2.id


def test_create_many_kickstarter_sales(authed_client, user):
    """Test bulk creating Kickstarter sales."""
    a1 = make_author(name="Bulk KS Author")
    b1 = make_book(isbn_13="9780000000063", author=a1,
                   cover_price="20.00", print_cost="10.00")

    payload = [
        {
            "book": b1.id,
            "quantity": 10,
            "sale_source": "kickstarter",
            "format": "print",
            "date": "2023-01",
        },
        {
            "book": b1.id,
            "quantity": 5,
            "sale_source": "kickstarter",
            "format": "ebook",
            "date": "2023-02",
        },
    ]

    resp = authed_client.post("/api/sales/create-many/", payload, format="json")
    assert resp.status_code == 201, resp.content
    assert len(resp.data) == 2

    # Verify computed revenue/royalty
    sale1 = Sale.objects.get(id=resp.data[0]["id"])
    assert sale1.publisher_revenue == Decimal("100.00")  # 10 * (20-10)

    sale2 = Sale.objects.get(id=resp.data[1]["id"])
    assert sale2.publisher_revenue == Decimal("50.00")   # 5 * (20-10)


def test_edit_kickstarter_sale(authed_client, user):
    """Test editing a Kickstarter sale recalculates revenue and royalty."""
    a1 = make_author(name="Edit KS Author")
    b1 = make_book(isbn_13="9780000000064", author=a1,
                   cover_price="20.00", print_cost="10.00")

    # Create via API
    payload = {
        "book": b1.id,
        "quantity": 10,
        "sale_source": "kickstarter",
        "date": "2023-01",
    }
    create_resp = authed_client.post("/api/sales/", payload, format="json")
    assert create_resp.status_code == 201
    sale_id = create_resp.data["id"]

    # Update quantity
    edit_payload = {"quantity": 20}
    resp = authed_client.patch(f"/api/sales/{sale_id}/", edit_payload, format="json")
    assert resp.status_code == 200

    sale = Sale.objects.get(id=sale_id)
    # Recomputed: 20 * (20 - 10) = 200.00
    assert sale.publisher_revenue == Decimal("200.00")
    # Royalty: 200 * 0.20 = 40.00
    assert sale.author_royalty == Decimal("40.00")


def test_export_csv_kickstarter(authed_client, user):
    """Test that Kickstarter records display correctly in CSV export."""
    a1 = make_author(name="CSV KS Author")
    b1 = make_book(isbn_13="9780000000065", title="KS CSV Book", author=a1,
                   cover_price="20.00", print_cost="10.00")

    Sale.objects.create(
        book=b1, quantity=10, publisher_revenue=Decimal("100.00"),
        publisher_revenue_original=Decimal("100.00"),
        author_royalty=Decimal("20.00"), sale_source="kickstarter",
        distributor=None, format="print",
        currency="USD", date="2023-07-01", comment="ks campaign"
    )

    resp = authed_client.get("/api/sales/export-csv/")
    assert resp.status_code == 200

    content = resp.content.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(content)))

    row = rows[1]
    assert row[0] == "2023-07"
    assert row[1] == "KS CSV Book"
    assert row[2] == "CSV KS Author"
    assert row[3] == "Kickstarter"    # source display
    assert row[4] == "N/A"            # distributor
    assert row[5] == "Print"
    assert row[6] == "10"             # quantity
    assert row[7] == "N/A"            # KENP
    assert row[8] == "USD"
    assert row[13] == "False"          # isProjected?
    assert row[14] == "ks campaign"

