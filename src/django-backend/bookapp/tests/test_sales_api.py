import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from decimal import Decimal

from bookapp.models import Book, Author, Sale, AuthorSale, AuthorBook

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

def make_author(name="Frank Herbert"):
    return Author.objects.create(name=name)

def make_book(*, publisher_user, isbn_13, title="T", author=None, royalty_rate="0.10"):
    book = Book.objects.create(
        title=title,
        publication_date="2000-01-01",
        isbn_13=isbn_13,
        isbn_10=None,
        total_sales_to_date=0,
        publisher_user=publisher_user,
    )
    if author is not None:
        # Create AuthorBook with specific rate
        AuthorBook.objects.create(author=author, book=book, royalty_rate=Decimal(royalty_rate))
    return book

def test_create_sale_creates_author_sale_records(authed_client, user):
    a1 = make_author()
    b1 = make_book(publisher_user=user, isbn_13="9780000000001", author=a1, royalty_rate="0.10")

    payload = {
        "book": b1.id,
        "quantity": 100,
        "publisher_revenue": "1000.00"
    }

    resp = authed_client.post("/api/sale/create", payload, format="json")
    assert resp.status_code == 201, resp.content

    assert Sale.objects.count() == 1
    sale = Sale.objects.first()
    assert sale.quantity == 100
    assert sale.publisher_revenue == Decimal("1000.00")

    # Check AuthorSale
    assert AuthorSale.objects.count() == 1
    as_record = AuthorSale.objects.first()
    assert as_record.author == a1
    assert as_record.sale == sale
    # 1000 * 0.10 = 100.00
    assert as_record.royalty_amount == Decimal("100.00")
    assert as_record.author_paid is False

def test_create_sale_with_royalty_override(authed_client, user):
    a1 = make_author()
    b1 = make_book(publisher_user=user, isbn_13="9780000000002", author=a1, royalty_rate="0.10")

    payload = {
        "book": b1.id,
        "quantity": 100,
        "publisher_revenue": "1000.00",
        "author_royalties": {
            str(a1.id): "500.00"
        },
        "author_paid": {
            str(a1.id): True
        }
    }

    resp = authed_client.post("/api/sale/create", payload, format="json")
    assert resp.status_code == 201, resp.content

    as_record = AuthorSale.objects.first()
    assert as_record.royalty_amount == Decimal("500.00")
    assert as_record.author_paid is True

def test_create_many_sales(authed_client, user):
    a1 = make_author()
    b1 = make_book(publisher_user=user, isbn_13="9780000000003", author=a1)

    payload = [
        {
            "book": b1.id,
            "quantity": 10,
            "publisher_revenue": "100.00"
        },
        {
            "book": b1.id,
            "quantity": 20,
            "publisher_revenue": "200.00"
        }
    ]

    resp = authed_client.post("/api/sale/createmany", payload, format="json")
    assert resp.status_code == 201, resp.content
    
    assert Sale.objects.count() == 2
    assert AuthorSale.objects.count() == 2

def test_get_all_sales_filtering(authed_client, user):
    a1 = make_author()
    b1 = make_book(publisher_user=user, isbn_13="9780000000004", title="Book1", author=a1)
    
    # Create another user and book
    u2 = User.objects.create_user(username="u2", password="password")
    b2 = make_book(publisher_user=u2, isbn_13="9780000000005", title="Book2", author=a1)

    # Sale for Book 1
    s1 = Sale.objects.create(book=b1, quantity=10, publisher_revenue=100)
    s1.create_author_sales()
    # Sale for Book 2
    s2 = Sale.objects.create(book=b2, quantity=10, publisher_revenue=100)
    s2.create_author_sales()

    # Test Filter by Book
    resp = authed_client.get(f"/api/sale/get_all?book_id={b1.id}")
    assert resp.status_code == 200
    assert len(resp.data) == 1
    assert resp.data[0]['book'] == b1.id

    # Test Filter by User (publisher)
    resp2 = authed_client.get(f"/api/sale/get_all?user_id={user.id}")
    assert resp2.status_code == 200
    assert len(resp2.data) == 1
    assert resp2.data[0]['book'] == b1.id
    
    # Verify extra fields in response
    sale_data = resp2.data[0]
    assert 'author_royalties' in sale_data
    assert 'author_paid' in sale_data
    # author_royalties should have entry for a1
    assert str(a1.id) in sale_data['author_royalties']
    assert str(a1.id) in sale_data['author_paid']

def test_edit_sale_updates_fields_and_royalties(authed_client, user):
    a1 = make_author()
    b1 = make_book(publisher_user=user, isbn_13="9780000000006", author=a1, royalty_rate="0.10")
    
    sale = Sale.objects.create(book=b1, quantity=10, publisher_revenue=Decimal("100.00"))
    # Initial AuthorSale (100 * 0.10 = 10.00)
    sale.create_author_sales() 
    
    payload = {
        "quantity": 20,
        "publisher_revenue": "200.00",
        "author_royalties": {
            str(a1.id): "50.00" # Override
        }
    }
    
    resp = authed_client.post(f"/api/sale/{sale.id}/edit", payload, format="json")
    assert resp.status_code == 200
    
    sale.refresh_from_db()
    assert sale.quantity == 20
    assert sale.publisher_revenue == Decimal("200.00")
    
    # Check AuthorSale updated
    as_record = AuthorSale.objects.get(sale=sale)
    assert as_record.royalty_amount == Decimal("50.00")

def test_edit_sale_updates_author_paid(authed_client, user):
    a1 = make_author()
    b1 = make_book(publisher_user=user, isbn_13="9780000000008", author=a1, royalty_rate="0.10")
    
    # Create sale where author is NOT paid
    sale = Sale.objects.create(book=b1, quantity=10, publisher_revenue=Decimal("100.00"))
    sale.create_author_sales() # author_paid defaults to False
    
    assert AuthorSale.objects.get(sale=sale).author_paid is False
    
    # Update to set author_paid = True
    payload = {
        "author_paid": {
            str(a1.id): True
        }
    }
    
    resp = authed_client.post(f"/api/sale/{sale.id}/edit", payload, format="json")
    assert resp.status_code == 200
    
    # Verify updated
    as_record = AuthorSale.objects.get(sale=sale)
    assert as_record.author_paid is True
    
    # Update back to False
    payload2 = {
        "author_paid": {
            str(a1.id): False
        }
    }
    resp2 = authed_client.post(f"/api/sale/{sale.id}/edit", payload2, format="json")
    assert resp2.status_code == 200
    
    # Re-fetch new object
    as_record = AuthorSale.objects.get(sale=sale)
    assert as_record.author_paid is False

def test_delete_sale(authed_client, user):
    a1 = make_author()
    b1 = make_book(publisher_user=user, isbn_13="9780000000007", author=a1)
    sale = Sale.objects.create(book=b1, quantity=10, publisher_revenue=100)
    
    resp = authed_client.delete(f"/api/sale/{sale.id}")
    assert resp.status_code == 204
    
    assert Sale.objects.count() == 0
