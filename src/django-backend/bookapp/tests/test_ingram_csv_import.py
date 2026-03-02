import io
import re
import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from bookapp.models import Book, Author, Sale

pytestmark = pytest.mark.django_db

SAMPLE_CSV_HEADER = "ISBN,Title,Author,Format,Gross Qty,Returned Qty,Net Qty,Net Compensation,Sales Market"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user():
    return User.objects.create_user(username="csvuser", password="pass12345")

@pytest.fixture
def authed_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


def make_book(isbn_13, title="Test Book", author_name="Test Author", royalty_rate="0.10",
              pub_date="2020-01-01", isbn_10=None):
    author, _ = Author.objects.get_or_create(
        name=author_name,
        defaults={"email": f"{author_name.lower().replace(' ', '_')}@test.com"},
    )
    book = Book.objects.create(
        title=title, publication_date=pub_date,
        isbn_13=isbn_13, isbn_10=isbn_10,
        author=author,
        distributor_author_royalty_rate=Decimal(royalty_rate),
        hand_sold_author_royalty_rate=Decimal("0.20"), # Default for tests
        cover_price=Decimal("20.00"), # Default for tests
        print_cost=Decimal("10.00"), # Default for tests
    )
    return book

@pytest.fixture
def sample_book():
    a = Author.objects.create(name="Frank Herbert")
    book = Book.objects.create(
        title="Dune",
        publication_date="1965-08-01",
        isbn_13="9780441172719",
        author=a,
        distributor_author_royalty_rate=Decimal("0.10"),
        hand_sold_author_royalty_rate=Decimal("0.20"),
        cover_price=Decimal("20.00"),
        print_cost=Decimal("10.00"),
    )
    return book


def build_csv(*data_rows, header=SAMPLE_CSV_HEADER, include_footer=True):
    """Build a CSV string with optional Ingram-style footer (blank + totals row)."""
    lines = [header]
    for row in data_rows:
        lines.append(row)
    if include_footer:
        lines.append(",,,,,,,," )  # blank row
        lines.append(",,,,,,,278.44,")  # totals row
    return "\n".join(lines) + "\n"


def upload(client, csv_content, month=9, year=2025, filename="Ingram-202509.csv"):
    csv_file = SimpleUploadedFile(filename, csv_content.encode("utf-8"), content_type="text/csv")
    return client.post(
        "/api/sales/import-ingram-csv/",
        {"file": csv_file, "month": month, "year": year},
        format="multipart",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestIngramCSVHappyPath:
    def test_single_row(self, authed_client):
        make_book("9781473619814", title="The Long Way", royalty_rate="0.15")
        csv = build_csv(
            '9781473619814,"The Long Way to a Small, Angry Planet","Chambers, Becky",Paperback,5,0,5,18.05,US'
        )
        resp = upload(authed_client, csv)
        assert resp.status_code == 200, resp.data

        preview = resp.data["preview"]
        assert len(preview) == 1

        row = preview[0]
        assert row["book_title"] == "The Long Way"
        assert row["quantity"] == 5
        assert row["sale_source"] == "distributor"
        assert row["publisher_revenue"] == "18.05"
        assert row["author_paid"] is False
        assert row["date"] == "2025-09"
        # author_royalty = 0.15 * 18.05 = 2.7075 → 2.71
        assert row["author_royalty"] == "2.71"
        # comment format
        assert "Ingram: Format='Paperback' Market='US'" in row["comment"]
        assert "File='Ingram-202509.csv'" in row["comment"]

    def test_multiple_rows(self, authed_client):
        make_book("9781473619814", title="Book A", author_name="Author A", royalty_rate="0.10")
        make_book("9780062569400", title="Book B", author_name="Author B", royalty_rate="0.20")
        csv = build_csv(
            '9781473619814,"Book A","Author A",Paperback,5,0,5,18.05,US',
            '9780062569400,"Book B","Author B",Paperback,3,0,3,15.42,US',
        )
        resp = upload(authed_client, csv)
        assert resp.status_code == 200
        assert len(resp.data["preview"]) == 2

    def test_isbn10_lookup(self, authed_client):
        make_book("9780000000099", title="ISBN10 Book", isbn_10="0765397539", royalty_rate="0.10")
        csv = build_csv(
            '0765397539,"Some Title","Some Author",Paperback,2,0,2,10.00,US'
        )
        resp = upload(authed_client, csv)
        assert resp.status_code == 200
        assert len(resp.data["preview"]) == 1
        assert resp.data["preview"][0]["book_title"] == "ISBN10 Book"

    def test_blank_row_stops_parsing(self, authed_client):
        """Verify parser stops at blank row and doesn't try to import the totals."""
        make_book("9781473619814", title="Book A", royalty_rate="0.10")
        csv = build_csv(
            '9781473619814,"Book A","Author",Paperback,5,0,5,18.05,US',
        )
        resp = upload(authed_client, csv)
        assert resp.status_code == 200
        assert len(resp.data["preview"]) == 1


class TestIngramCSVColumnValidation:
    def test_missing_columns(self, authed_client):
        csv_content = "ISBN,Title,Author\n9781473619814,Test,Author\n"
        resp = upload(authed_client, csv_content)
        assert resp.status_code == 400
        assert any("Missing columns" in e for e in resp.data["errors"])

    def test_extra_columns(self, authed_client):
        csv_content = (
            SAMPLE_CSV_HEADER + ",Extra\n"
            "9781473619814,T,A,Paperback,5,0,5,18.05,US,extra\n"
        )
        resp = upload(authed_client, csv_content)
        assert resp.status_code == 400
        assert any("Unexpected columns" in e for e in resp.data["errors"])

    def test_extra_field_on_single_row(self, authed_client):
        """No extra header, but one specific row has extra trailing data."""
        make_book("9781473619814", title="Book A", royalty_rate="0.10")
        csv_content = (
            SAMPLE_CSV_HEADER + "\n"
            '9781473619814,"Book A","Author",Paperback,5,0,5,18.05,US,oops_extra_data\n'
        )
        resp = upload(authed_client, csv_content)
        assert resp.status_code == 400
        assert any("unexpected extra column" in e for e in resp.data["errors"])

    def test_trailing_empty_columns_fail(self, authed_client):
        """Excel/Numbers sometimes append empty trailing columns; we strictly reject them."""
        make_book("9781473619814", title="Book A", royalty_rate="0.10")
        csv_content = (
            SAMPLE_CSV_HEADER + ",\n"
            '9781473619814,"Book A","Author",Paperback,5,0,5,18.05,US,\n'
        )
        resp = upload(authed_client, csv_content)
        assert resp.status_code == 400
        assert any("Unexpected columns" in e for e in resp.data["errors"])

    def test_wrong_column_order(self, authed_client):
        wrong_header = "Title,ISBN,Author,Format,Gross Qty,Returned Qty,Net Qty,Net Compensation,Sales Market"
        csv_content = wrong_header + "\n" + "T,9781473619814,A,Paperback,5,0,5,18.05,US\n"
        resp = upload(authed_client, csv_content)
        assert resp.status_code == 400
        assert any("wrong order" in e for e in resp.data["errors"])


class TestIngramCSVRowValidation:
    def test_returned_qty_nonzero(self, authed_client):
        make_book("9781473619814", title="Book")
        csv = build_csv(
            '9781473619814,"Book","Author",Paperback,5,2,3,18.05,US'
        )
        resp = upload(authed_client, csv)
        assert resp.status_code == 400
        assert any("Returned Qty must be zero (got 2)" in e for e in resp.data["errors"])

    def test_net_qty_not_equal_gross_qty(self, authed_client):
        make_book("9781473619814", title="Book")
        csv = build_csv(
            '9781473619814,"Book","Author",Paperback,5,0,3,18.05,US'
        )
        resp = upload(authed_client, csv)
        assert resp.status_code == 400
        assert any("Net Qty (3) does not equal Gross Qty (5)" in e for e in resp.data["errors"])

    def test_unknown_isbn(self, authed_client):
        csv = build_csv(
            '9789999999999,"Unknown","Author",Paperback,5,0,5,18.05,US'
        )
        resp = upload(authed_client, csv)
        assert resp.status_code == 400
        assert any("No book found with ISBN '9789999999999'" in e for e in resp.data["errors"])

    def test_invalid_gross_qty(self, authed_client):
        make_book("9781473619814", title="Book")
        csv = build_csv(
            '9781473619814,"Book","Author",Paperback,abc,0,5,18.05,US'
        )
        resp = upload(authed_client, csv)
        assert resp.status_code == 400
        assert any("Gross Qty" in e and "valid integer" in e for e in resp.data["errors"])

    def test_invalid_net_compensation(self, authed_client):
        make_book("9781473619814", title="Book")
        csv = build_csv(
            '9781473619814,"Book","Author",Paperback,5,0,5,abc,US'
        )
        resp = upload(authed_client, csv)
        assert resp.status_code == 400
        assert any("Net Compensation" in e for e in resp.data["errors"])

    def test_negative_net_compensation(self, authed_client):
        make_book("9781473619814", title="Book")
        csv = build_csv(
            '9781473619814,"Book","Author",Paperback,5,0,5,-10.00,US'
        )
        resp = upload(authed_client, csv)
        assert resp.status_code == 400
        assert any("non-negative" in e for e in resp.data["errors"])

    def test_net_qty_zero(self, authed_client):
        make_book("9781473619814", title="Book")
        csv = build_csv(
            '9781473619814,"Book","Author",Paperback,0,0,0,0.00,US'
        )
        resp = upload(authed_client, csv)
        assert resp.status_code == 400
        assert any("Quantity must be a positive integer" in e for e in resp.data["errors"])

    def test_sale_date_before_publication(self, authed_client):
        make_book("9781473619814", title="Book", pub_date="2026-06-01")
        csv = build_csv(
            '9781473619814,"Book","Author",Paperback,5,0,5,18.05,US'
        )
        resp = upload(authed_client, csv, month=1, year=2025)
        assert resp.status_code == 400
        assert any("before" in e.lower() and "publication date" in e.lower() for e in resp.data["errors"])

    def test_multiple_errors_collected(self, authed_client):
        """Multiple rows with different errors should all be reported."""
        make_book("9781473619814", title="Book")
        csv = build_csv(
            '9781473619814,"Book","Author",Paperback,5,1,5,18.05,US',   # returned != 0
            '9789999999999,"Unknown","Author",Paperback,3,0,3,10.00,US',  # unknown ISBN
        )
        resp = upload(authed_client, csv)
        assert resp.status_code == 400
        assert len(resp.data["errors"]) >= 2

    def test_empty_textual_fields(self, authed_client):
        """Values like Title, Author, Format, Sales Market cannot be completely empty."""
        make_book("9781473619814", title="Book")
        csv = build_csv(
            '9781473619814,"","Author",Paperback,5,0,5,18.05,US',        # Empty Title
            '9781473619814,"Book","",Paperback,5,0,5,18.05,US',          # Empty Author
            '9781473619814,"Book","Author","",5,0,5,18.05,US',           # Empty Format
            '9781473619814,"Book","Author",Paperback,5,0,5,18.05,""',    # Empty Sales Market
        )
        resp = upload(authed_client, csv)
        assert resp.status_code == 400
        
        errors = "".join(resp.data["errors"])
        assert "Title cannot be empty" in errors
        assert "Author cannot be empty" in errors
        assert "Format cannot be empty" in errors
        assert "Sales Market cannot be empty" in errors


class TestIngramCSVRequestValidation:
    def test_no_file(self, authed_client):
        resp = authed_client.post(
            "/api/sales/import-ingram-csv/",
            {"month": 9, "year": 2025},
            format="multipart",
        )
        assert resp.status_code == 400
        assert any("No file" in e for e in resp.data["errors"])

    def test_invalid_month(self, authed_client):
        csv = build_csv()
        resp = upload(authed_client, csv, month=13, year=2025)
        assert resp.status_code == 400
        assert any("Month" in e for e in resp.data["errors"])

    def test_invalid_year(self, authed_client):
        csv = build_csv()
        resp = upload(authed_client, csv, month=1, year=0)
        assert resp.status_code == 400
        assert any("Year" in e for e in resp.data["errors"])

    def test_nothing_saved_on_validation_failure(self, authed_client):
        """Validate endpoint is preview-only; no Sale records should be created."""
        from bookapp.models import Sale
        make_book("9781473619814", title="Book")
        csv = build_csv(
            '9781473619814,"Book","Author",Paperback,5,0,5,18.05,US',
            '9789999999999,"Unknown","Author",Paperback,3,0,3,10.00,US',  # will fail
        )
        resp = upload(authed_client, csv)
        assert resp.status_code == 400
        assert Sale.objects.count() == 0

    def test_unauthenticated_rejected(self, api_client):
        csv = build_csv()
        csv_file = SimpleUploadedFile("test.csv", csv.encode("utf-8"), content_type="text/csv")
        resp = api_client.post(
            "/api/sales/import-ingram-csv/",
            {"file": csv_file, "month": 9, "year": 2025},
            format="multipart",
        )
        assert resp.status_code in (401, 403)


class TestIngramCSVCommentAndRoyalty:
    def test_comment_format(self, authed_client):
        make_book("9781473619814", title="Book", royalty_rate="0.10")
        csv = build_csv(
            '9781473619814,"Book","Author",Hardcover,5,0,5,18.05,UK'
        )
        resp = upload(authed_client, csv, month=3, year=2024)
        assert resp.status_code == 200
        comment = resp.data["preview"][0]["comment"]
        # Spec format: Ingram: Format='[Format]' Market='[Sales Market]' File='[Filename]' ([Timestamp])
        # Timestamp must be YYYY-MM-DD HH:MM:SS with no trailing timezone name
        assert re.search(
            r"^Ingram: Format='Hardcover' Market='UK' File='Ingram-202509\.csv' "
            r"\(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\)$",
            comment,
        ), f"Comment did not match expected format: {comment!r}"

    def test_royalty_computation(self, authed_client):
        make_book("9781473619814", title="Book", royalty_rate="0.25")
        csv = build_csv(
            '9781473619814,"Book","Author",Paperback,10,0,10,100.00,US'
        )
        resp = upload(authed_client, csv)
        assert resp.status_code == 200
        # 0.25 * 100.00 = 25.00
        assert resp.data["preview"][0]["author_royalty"] == "25.00"
