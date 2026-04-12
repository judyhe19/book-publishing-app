# views/royalty_report.py
# Author royalty report endpoint — aggregates sales by book × quarter

from decimal import Decimal

from django.db.models import Sum, Case, When, Value, DecimalField, IntegerField, F
from django.db.models.functions import Coalesce

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Author, Book, Sale


# Quarter date ranges
QUARTER_RANGES = {
    1: ("01-01", "03-31"),
    2: ("04-01", "06-30"),
    3: ("07-01", "09-30"),
    4: ("10-01", "12-31"),
}


def _quarter_date_range(year, quarter):
    """Return (start_date, end_date) strings for a given year/quarter."""
    start_md, end_md = QUARTER_RANGES[quarter]
    return f"{year:04d}-{start_md}", f"{year:04d}-{end_md}"


def _enumerate_quarters(start_year, start_quarter, end_year, end_quarter):
    """Yield (year, quarter) tuples from start to end inclusive."""
    y, q = start_year, start_quarter
    while (y, q) <= (end_year, end_quarter):
        yield y, q
        q += 1
        if q > 4:
            q = 1
            y += 1


def _aggregate_sales(sales_qs):
    """Aggregate a queryset of Sale objects into report metrics."""
    agg = sales_qs.aggregate(
        quantity_sold_print_handsold=Coalesce(
            Sum(
                Case(
                    When(
                        sale_source="handsold",
                        format="print",
                        then=Coalesce(F("quantity"), Value(0)),
                    ),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ),
            Value(0),
            output_field=IntegerField(),
        ),
        quantity_sold_print_kickstarter=Coalesce(
            Sum(
                Case(
                    When(
                        sale_source="kickstarter",
                        format="print",
                        then=Coalesce(F("quantity"), Value(0)),
                    ),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ),
            Value(0),
            output_field=IntegerField(),
        ),
        quantity_sold_print_ingram_spark=Coalesce(
            Sum(
                Case(
                    When(
                        sale_source="distributor",
                        distributor="Ingram Spark",
                        format="print",
                        then=Coalesce(F("quantity"), Value(0)),
                    ),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ),
            Value(0),
            output_field=IntegerField(),
        ),
        quantity_sold_print_amazon=Coalesce(
            Sum(
                Case(
                    When(
                        sale_source="distributor",
                        distributor="Amazon",
                        format="print",
                        then=Coalesce(F("quantity"), Value(0)),
                    ),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ),
            Value(0),
            output_field=IntegerField(),
        ),
        quantity_sold_ebook_kickstarter=Coalesce(
            Sum(
                Case(
                    When(
                        sale_source="kickstarter",
                        format="ebook",
                        then=Coalesce(F("quantity"), Value(0)),
                    ),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ),
            Value(0),
            output_field=IntegerField(),
        ),
        quantity_sold_ebook_amazon=Coalesce(
            Sum(
                Case(
                    When(
                        sale_source="distributor",
                        distributor="Amazon",
                        format="ebook",
                        then=Coalesce(F("quantity"), Value(0)),
                    ),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ),
            Value(0),
            output_field=IntegerField(),
        ),
        quantity_sold_print_other=Coalesce(
            Sum(
                Case(
                    When(
                        sale_source="distributor",
                        distributor="Other",
                        format="print",
                        then=Coalesce(F("quantity"), Value(0)),
                    ),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ),
            Value(0),
            output_field=IntegerField(),
        ),
        quantity_sold_ebook_other=Coalesce(
            Sum(
                Case(
                    When(
                        sale_source="distributor",
                        distributor="Other",
                        format="ebook",
                        then=Coalesce(F("quantity"), Value(0)),
                    ),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ),
            Value(0),
            output_field=IntegerField(),
        ),
        kenp=Coalesce(
            Sum(
                Case(
                    When(
                        sale_source="distributor",
                        distributor="Amazon",
                        format="kindle unlimited",
                        then=Coalesce(F("kenp"), Value(0)),
                    ),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ),
            Value(0),
            output_field=IntegerField(),
        ),
        royalty_unpaid=Coalesce(
            Sum(
                Case(
                    When(author_paid=False, then="author_royalty"),
                    default=Value(0),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            ),
            Value(0),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
        royalty_paid=Coalesce(
            Sum(
                Case(
                    When(author_paid=True, then="author_royalty"),
                    default=Value(0),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            ),
            Value(0),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
        royalty_total=Coalesce(
            Sum("author_royalty"),
            Value(0),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
    )

    quantity_sold_total = (
        agg["quantity_sold_print_handsold"]
        + agg["quantity_sold_print_kickstarter"]
        + agg["quantity_sold_print_ingram_spark"]
        + agg["quantity_sold_print_amazon"]
        + agg["quantity_sold_ebook_kickstarter"]
        + agg["quantity_sold_ebook_amazon"]
        + agg["quantity_sold_print_other"]
        + agg["quantity_sold_ebook_other"]
    )
    return {
        "quantity_sold_print_handsold": agg["quantity_sold_print_handsold"],
        "quantity_sold_print_kickstarter": agg["quantity_sold_print_kickstarter"],
        "quantity_sold_print_ingram_spark": agg["quantity_sold_print_ingram_spark"],
        "quantity_sold_print_amazon": agg["quantity_sold_print_amazon"],
        "quantity_sold_ebook_kickstarter": agg["quantity_sold_ebook_kickstarter"],
        "quantity_sold_ebook_amazon": agg["quantity_sold_ebook_amazon"],
        "quantity_sold_print_other": agg["quantity_sold_print_other"],
        "quantity_sold_ebook_other": agg["quantity_sold_ebook_other"],
        "quantity_sold_total": quantity_sold_total,
        "kenp": agg["kenp"],
        "royalty_unpaid": str(agg["royalty_unpaid"]),
        "royalty_paid": str(agg["royalty_paid"]),
        "royalty_total": str(agg["royalty_total"]),
    }


class AuthorRoyaltyReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, author_id):
        # --- Validate author ---
        try:
            author = Author.objects.get(pk=author_id)
        except Author.DoesNotExist:
            return Response(
                {"detail": "Author not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # --- Parse & validate quarter params ---
        try:
            start_year = int(request.query_params["start_year"])
            start_quarter = int(request.query_params["start_quarter"])
            end_year = int(request.query_params["end_year"])
            end_quarter = int(request.query_params["end_quarter"])
        except (KeyError, ValueError, TypeError):
            return Response(
                {"detail": "start_year, start_quarter, end_year, and end_quarter are required integers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (1 <= start_quarter <= 4 and 1 <= end_quarter <= 4):
            return Response(
                {"detail": "Quarters must be between 1 and 4."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if (start_year, start_quarter) > (end_year, end_quarter):
            return Response(
                {"detail": "Start quarter must not be after end quarter."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- Get author's books, sorted: series books first by (series_name, series_position), then non-series by title ---
        books = list(
            Book.objects.filter(author=author)
            .annotate(
                has_no_series=Case(
                    When(series_name__isnull=True, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            )
            .order_by("has_no_series", "series_name", "series_position", "title")
        )

        # Build quarters list
        quarters = []
        for y, q in _enumerate_quarters(start_year, start_quarter, end_year, end_quarter):
            quarters.append({"year": y, "quarter": q, "label": f"{y} Q{q}"})

        # All sales for this author's books
        all_author_sales = Sale.objects.filter(book__author=author)

        # Overall date range for the selected period
        overall_start, _ = _quarter_date_range(start_year, start_quarter)
        _, overall_end = _quarter_date_range(end_year, end_quarter)
        selected_period_sales = all_author_sales.filter(
            date__gte=overall_start, date__lte=overall_end
        )

        # --- Build per-book data ---
        data = {}
        for book in books:
            book_sales = all_author_sales.filter(book=book)
            book_data = {}

            # Per-quarter
            for qinfo in quarters:
                sd, ed = _quarter_date_range(qinfo["year"], qinfo["quarter"])
                qs = book_sales.filter(date__gte=sd, date__lte=ed)
                book_data[qinfo["label"]] = _aggregate_sales(qs)

            # Selected-period total for this book
            book_data["All Time"] = _aggregate_sales(
                book_sales.filter(date__gte=overall_start, date__lte=overall_end)
            )

            data[book.id] = book_data

        # --- Build all-books totals ---
        totals = {}
        for qinfo in quarters:
            sd, ed = _quarter_date_range(qinfo["year"], qinfo["quarter"])
            qs = all_author_sales.filter(date__gte=sd, date__lte=ed)
            totals[qinfo["label"]] = _aggregate_sales(qs)

        totals["All Time"] = _aggregate_sales(selected_period_sales)

        # --- Serialize books ---
        books_out = []
        for book in books:
            books_out.append({
                "id": book.id,
                "title": book.title,
                "isbn_13": book.isbn_13,
                "series_name": book.series_name,
                "series_position": book.series_position,
                "series_display": book.series_display,
            })

        return Response({
            "author": {"id": author.id, "name": author.name},
            "books": books_out,
            "quarters": quarters,
            "data": data,
            "totals": totals,
        })
