import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from bookapp.models import Author, Book, Sale

pytestmark = pytest.mark.django_db

import uuid


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(username="rpt_user", password="pass12345")


@pytest.fixture
def authed_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


def make_author(name="Report Author"):
    email = f"{name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:6]}@test.com"
    return Author.objects.create(name=name, email=email)


def make_book(*, isbn_13, title, author, series_name=None, series_position=None):
    return Book.objects.create(
        title=title,
        publication_date="2000-01-01",
        isbn_13=isbn_13,
        author=author,
        distributor_author_royalty_rate=Decimal("0.10"),
        hand_sold_author_royalty_rate=Decimal("0.20"),
        cover_price=Decimal("20.00"),
        print_cost=Decimal("10.00"),
        series_name=series_name,
        series_position=series_position,
    )


def make_sale(book, date, quantity=10, revenue="100.00", source="distributor", paid=False):
    distributor = "Ingram Spark" if source == "distributor" else None
    if source in ("handsold", "kickstarter"):
        royalty = Decimal(revenue) * book.hand_sold_author_royalty_rate
    else:
        royalty = Decimal(revenue) * book.distributor_author_royalty_rate
    return Sale.objects.create(
        book=book,
        date=date,
        quantity=quantity,
        publisher_revenue=Decimal(revenue),
        author_royalty=royalty,
        sale_source=source,
        distributor=distributor,
        format="print",
        author_paid=paid,
    )


class TestRoyaltyReportStructure:

    def test_report_returns_correct_structure(self, authed_client):
        author = make_author("Alice")
        book = make_book(isbn_13="9780000000101", title="Book A", author=author)
        make_sale(book, "2025-01-15")

        resp = authed_client.get(
            f"/api/authors/{author.id}/royalty-report/",
            {"start_year": 2025, "start_quarter": 1, "end_year": 2025, "end_quarter": 1},
        )
        assert resp.status_code == 200

        data = resp.data
        assert data["author"]["id"] == author.id
        assert data["author"]["name"] == "Alice"
        assert len(data["books"]) == 1
        assert len(data["quarters"]) == 1
        assert data["quarters"][0]["label"] == "2025 Q1"
        assert str(book.id) in data["data"] or book.id in data["data"]
        assert "totals" in data

    def test_report_requires_auth(self, api_client):
        author = make_author("Unauthed")
        resp = api_client.get(
            f"/api/authors/{author.id}/royalty-report/",
            {"start_year": 2025, "start_quarter": 1, "end_year": 2025, "end_quarter": 1},
        )
        assert resp.status_code in (401, 403)

    def test_invalid_quarter_params(self, authed_client):
        author = make_author("Bad Params")

        # Missing params
        resp = authed_client.get(f"/api/authors/{author.id}/royalty-report/")
        assert resp.status_code == 400

        # Quarter out of range
        resp = authed_client.get(
            f"/api/authors/{author.id}/royalty-report/",
            {"start_year": 2025, "start_quarter": 5, "end_year": 2025, "end_quarter": 1},
        )
        assert resp.status_code == 400

        # Start after end
        resp = authed_client.get(
            f"/api/authors/{author.id}/royalty-report/",
            {"start_year": 2026, "start_quarter": 1, "end_year": 2025, "end_quarter": 4},
        )
        assert resp.status_code == 400

    def test_nonexistent_author(self, authed_client):
        resp = authed_client.get(
            "/api/authors/99999/royalty-report/",
            {"start_year": 2025, "start_quarter": 1, "end_year": 2025, "end_quarter": 1},
        )
        assert resp.status_code == 404


class TestRoyaltyReportAggregation:

    def test_quarterly_aggregation(self, authed_client):
        author = make_author("Bob")
        book = make_book(isbn_13="9780000000201", title="Q Book", author=author)

        # Q1 2025 sale
        make_sale(book, "2025-02-15", quantity=10, revenue="100.00")
        # Q2 2025 sale
        make_sale(book, "2025-05-15", quantity=20, revenue="200.00")

        resp = authed_client.get(
            f"/api/authors/{author.id}/royalty-report/",
            {"start_year": 2025, "start_quarter": 1, "end_year": 2025, "end_quarter": 2},
        )
        assert resp.status_code == 200

        book_data = resp.data["data"][book.id]

        # Q1
        assert book_data["2025 Q1"]["quantity_sold_total"] == 10
        assert Decimal(book_data["2025 Q1"]["royalty_total"]) == Decimal("10.00")

        # Q2
        assert book_data["2025 Q2"]["quantity_sold_total"] == 20
        assert Decimal(book_data["2025 Q2"]["royalty_total"]) == Decimal("20.00")

    def test_handsold_quantity(self, authed_client):
        author = make_author("Carol")
        book = make_book(isbn_13="9780000000301", title="Handsold Book", author=author)

        make_sale(book, "2025-01-15", quantity=10, revenue="100.00", source="distributor")
        make_sale(book, "2025-02-15", quantity=5, revenue="50.00", source="handsold")

        resp = authed_client.get(
            f"/api/authors/{author.id}/royalty-report/",
            {"start_year": 2025, "start_quarter": 1, "end_year": 2025, "end_quarter": 1},
        )
        assert resp.status_code == 200

        book_data = resp.data["data"][book.id]["2025 Q1"]
        assert book_data["quantity_sold_total"] == 15  # 10 + 5
        assert book_data["quantity_sold_print_handsold"] == 5

    def test_paid_unpaid_split(self, authed_client):
        author = make_author("Dave")
        book = make_book(isbn_13="9780000000401", title="Paid Book", author=author)

        # Paid sale: 100 * 0.10 = $10 royalty
        make_sale(book, "2025-01-15", quantity=10, revenue="100.00", paid=True)
        # Unpaid sale: 200 * 0.10 = $20 royalty
        make_sale(book, "2025-02-15", quantity=20, revenue="200.00", paid=False)

        resp = authed_client.get(
            f"/api/authors/{author.id}/royalty-report/",
            {"start_year": 2025, "start_quarter": 1, "end_year": 2025, "end_quarter": 1},
        )
        assert resp.status_code == 200

        book_data = resp.data["data"][book.id]["2025 Q1"]
        assert Decimal(book_data["royalty_paid"]) == Decimal("10.00")
        assert Decimal(book_data["royalty_unpaid"]) == Decimal("20.00")
        assert Decimal(book_data["royalty_total"]) == Decimal("30.00")

    def test_all_time_totals(self, authed_client):
        author = make_author("Eve")
        book = make_book(isbn_13="9780000000501", title="All Time Book", author=author)

        # Sales in different quarters — and also one outside the query range
        make_sale(book, "2024-06-15", quantity=5, revenue="50.00")   # Q2 2024 (outside range)
        make_sale(book, "2025-01-15", quantity=10, revenue="100.00")  # Q1 2025
        make_sale(book, "2025-04-15", quantity=20, revenue="200.00")  # Q2 2025

        resp = authed_client.get(
            f"/api/authors/{author.id}/royalty-report/",
            {"start_year": 2025, "start_quarter": 1, "end_year": 2025, "end_quarter": 2},
        )
        assert resp.status_code == 200

        # All-time should include only sales within the selected quarter range
        all_time = resp.data["data"][book.id]["All Time"]
        assert all_time["quantity_sold_total"] == 30  # 10 + 20 (Q2 2024 sale is outside range)

        # Totals (all books) all-time
        totals_all_time = resp.data["totals"]["All Time"]
        assert totals_all_time["quantity_sold_total"] == 30

    def test_all_books_totals(self, authed_client):
        author = make_author("Frank")
        book1 = make_book(isbn_13="9780000000601", title="Book One", author=author)
        book2 = make_book(isbn_13="9780000000602", title="Book Two", author=author)

        make_sale(book1, "2025-01-15", quantity=10, revenue="100.00")
        make_sale(book2, "2025-01-15", quantity=20, revenue="200.00")

        resp = authed_client.get(
            f"/api/authors/{author.id}/royalty-report/",
            {"start_year": 2025, "start_quarter": 1, "end_year": 2025, "end_quarter": 1},
        )
        assert resp.status_code == 200

        totals = resp.data["totals"]["2025 Q1"]
        assert totals["quantity_sold_total"] == 30
        assert Decimal(totals["royalty_total"]) == Decimal("30.00")


class TestRoyaltyReportBookSorting:

    def test_series_books_before_non_series(self, authed_client):
        author = make_author("Gina")

        # Non-series book
        standalone = make_book(isbn_13="9780000000701", title="Zeta Standalone", author=author)
        # Series books
        series_b2 = make_book(isbn_13="9780000000702", title="Saga Part 2", author=author,
                              series_name="Saga", series_position=2)
        series_b1 = make_book(isbn_13="9780000000703", title="Saga Part 1", author=author,
                              series_name="Saga", series_position=1)

        resp = authed_client.get(
            f"/api/authors/{author.id}/royalty-report/",
            {"start_year": 2025, "start_quarter": 1, "end_year": 2025, "end_quarter": 1},
        )
        assert resp.status_code == 200

        book_ids = [b["id"] for b in resp.data["books"]]
        # Series books first (by position), then standalone
        assert book_ids == [series_b1.id, series_b2.id, standalone.id]

    def test_multiple_series_sorted(self, authed_client):
        author = make_author("Hugo")

        b_a1 = make_book(isbn_13="9780000000801", title="Alpha 1", author=author,
                         series_name="Alpha", series_position=1)
        b_b1 = make_book(isbn_13="9780000000802", title="Beta 1", author=author,
                         series_name="Beta", series_position=1)
        b_a2 = make_book(isbn_13="9780000000803", title="Alpha 2", author=author,
                         series_name="Alpha", series_position=2)
        standalone = make_book(isbn_13="9780000000804", title="Gamma", author=author)

        resp = authed_client.get(
            f"/api/authors/{author.id}/royalty-report/",
            {"start_year": 2025, "start_quarter": 1, "end_year": 2025, "end_quarter": 1},
        )
        assert resp.status_code == 200

        book_ids = [b["id"] for b in resp.data["books"]]
        # Alpha series first (by position), then Beta, then standalone
        assert book_ids == [b_a1.id, b_a2.id, b_b1.id, standalone.id]
