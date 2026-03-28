# views/sales.py
# Refactored to use ModelViewSet (Evolution 2: single author per book)

import csv
import calendar
import io
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.http import HttpResponse
from django.db.models import (
    Sum, Case, When, Value,
    IntegerField, DecimalField, F,
)
from django.db.models.functions import Coalesce, NullIf

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from ..models import Sale, Book
from ..serializers.sales import SaleSerializer, SaleWriteSerializer
from ..config.sort_config import SALES_SORT_FIELD_MAP, SALES_DEFAULT_SORT
from ..pagination import StandardPagination
from ..utils.ingram_csv import IngramSparkCSVParser
from ..utils.amazon_xlsx import AmazonXLSXParser

def money(x):
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class SaleViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update", "create_many"):
            return SaleWriteSerializer
        return SaleSerializer

    # ------------------------------------------------------------------
    # Queryset
    # ------------------------------------------------------------------

    def get_queryset(self):
        qs = Sale.objects.all()
        qs = qs.select_related("book", "book__author")

        # Filtering (on list and export_csv)
        if self.action in ("list", "export_csv"):
            book_id = self.request.query_params.get("book_id")
            user_id = self.request.query_params.get("user_id")
            author_name = self.request.query_params.get("author_name")
            sale_source = self.request.query_params.get("sale_source")
            distributor = self.request.query_params.get("distributor")
            sale_format = self.request.query_params.get("sale_format")

            if book_id:
                qs = qs.filter(book_id=book_id)
            if user_id:
                qs = qs.filter(book__publisher_user_id=user_id)
            if author_name:
                qs = qs.filter(book__author__name__icontains=author_name)
            if sale_source:
                qs = qs.filter(sale_source=sale_source)
            if distributor:
                qs = qs.filter(distributor=distributor)
            if sale_format:
                qs = qs.filter(format=sale_format)

            # Date filtering at month/year granularity
            start_date = self.request.query_params.get("start_date")
            end_date = self.request.query_params.get("end_date")

            if start_date:
                parts = start_date.split("-")
                first_of_month = f"{parts[0]}-{parts[1]}-01"
                qs = qs.filter(date__gte=first_of_month)

            if end_date:
                parts = end_date.split("-")
                year, month = int(parts[0]), int(parts[1])
                last_day = calendar.monthrange(year, month)[1]
                last_of_month = f"{year}-{month:02d}-{last_day:02d}"
                qs = qs.filter(date__lte=last_of_month)

            # Annotations for sorting
            # Evolution 2: single author on Book via FK
            qs = qs.annotate(
                first_author_name=F("book__author__name"),
            )

            # Ordering
            ordering = self.request.query_params.get("ordering", SALES_DEFAULT_SORT)
            is_desc = ordering.startswith("-")
            field = ordering[1:] if is_desc else ordering

            if field in SALES_SORT_FIELD_MAP:
                db_field = SALES_SORT_FIELD_MAP[field]
                # Treat empty strings as NULL for comment sorting
                if field == 'comment':
                    expr = NullIf(F(db_field), Value(''))
                    qs = qs.annotate(_comment_sort=expr)
                    if is_desc:
                        # null/empty first if descending
                        qs = qs.order_by(F('_comment_sort').desc(nulls_first=True))
                    else:
                        # null/empty last if ascending
                        qs = qs.order_by(F('_comment_sort').asc(nulls_last=True))
                elif field == 'publisher_revenue_original':
                    # Sort by currency type first, then by original amount
                    if is_desc:
                        qs = qs.order_by('-currency', F('publisher_revenue_original').desc(nulls_last=True))
                    else:
                        qs = qs.order_by('currency', F('publisher_revenue_original').asc(nulls_last=True))
                else:
                    order_field = ("-" if is_desc else "") + db_field
                    qs = qs.order_by(order_field)
            else:
                qs = qs.order_by("-date")

        return qs

    # ------------------------------------------------------------------
    # CREATE — single sale
    # ------------------------------------------------------------------

    def create(self, request, *args, **kwargs):
        serializer = SaleWriteSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                sale = serializer.save()
            full_serializer = SaleSerializer(sale)
            return Response(full_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------
    # CREATE MANY — bulk create (custom action)
    # ------------------------------------------------------------------

    @action(detail=False, methods=["post"], url_path="create-many")
    def create_many(self, request):
        if not isinstance(request.data, list):
            return Response({"error": "Expected a list of sales"}, status=status.HTTP_400_BAD_REQUEST)

        created_sales = []
        errors = []

        with transaction.atomic():
            for index, sale_data in enumerate(request.data):
                serializer = SaleWriteSerializer(data=sale_data)
                if serializer.is_valid():
                    sale = serializer.save()
                    created_sales.append(sale)
                else:
                    errors.append({"index": index, "errors": serializer.errors})

            if errors:
                transaction.set_rollback(True)
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        full_serializer = SaleSerializer(created_sales, many=True)
        return Response(full_serializer.data, status=status.HTTP_201_CREATED)

    # ------------------------------------------------------------------
    # IMPORT INGRAM CSV — validate + preview (custom action)
    # ------------------------------------------------------------------

    @action(detail=False, methods=["post"], url_path="import-ingram-csv",
            parser_classes=[MultiPartParser, FormParser])
    def import_ingram_csv(self, request):
        csv_file = request.FILES.get("file")
        if not csv_file:
            return Response(
                {"errors": ["No file uploaded."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            month = int(request.data.get("month", 0))
            year = int(request.data.get("year", 0))
        except (ValueError, TypeError):
            return Response(
                {"errors": ["Month and year must be integers."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (1 <= month <= 12):
            return Response(
                {"errors": ["Month must be between 1 and 12."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if year < 1:
            return Response(
                {"errors": ["Year must be a positive integer."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = IngramSparkCSVParser().parse_and_validate(csv_file, month=month, year=year)

        if result.errors:
            return Response({"errors": result.errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"preview": result.preview, **result.metadata},
            status=status.HTTP_200_OK,
        )

    # ------------------------------------------------------------------
    # IMPORT AMAZON XLSX — validate + preview (custom action)
    # ------------------------------------------------------------------

    @action(detail=False, methods=["post"], url_path="import-amazon-xlsx",
            parser_classes=[MultiPartParser, FormParser])
    def import_amazon_xlsx(self, request):
        xlsx_file = request.FILES.get("file")
        if not xlsx_file:
            return Response(
                {"errors": ["No file uploaded."], "warnings": []},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = AmazonXLSXParser().parse_and_validate(xlsx_file)

        if result.errors:
            return Response(
                {"errors": result.errors, "warnings": result.warnings},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"preview": result.preview, "warnings": result.warnings, **result.metadata},
            status=status.HTTP_200_OK,
        )

    # ------------------------------------------------------------------
    # UPDATE (PATCH) — edit a sale
    # ------------------------------------------------------------------

    def partial_update(self, request, *args, **kwargs):
        sale = self.get_object()

        fields_param = request.query_params.get("fields")
        data = request.data
        if fields_param:
            allowed_fields = fields_param.split(",")
            data = {k: v for k, v in request.data.items() if k in allowed_fields}

        serializer = SaleWriteSerializer(sale, data=data, partial=True)
        if serializer.is_valid():
            with transaction.atomic():
                updated_sale = serializer.save()

            full_serializer = SaleSerializer(updated_sale)
            return Response(full_serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Also support PUT as same behavior as PATCH
    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.partial_update(request, *args, **kwargs)

    # ------------------------------------------------------------------
    # EXPORT CSV — all filtered sales as CSV download
    # ------------------------------------------------------------------

    # Currencies that have no fractional unit (output whole numbers)
    ZERO_DECIMAL_CURRENCIES = {
        "JPY", "KRW", "ISK", "HUF", "IDR", "CLP", "VND",
    }

    CSV_HEADERS = [
        "Date", "Title", "Author", "Source", "Distributor",
        "Format", "Quantity", "KENP", "Original Currency",
        "Pub. Revenue (Original)", "Pub. Revenue (USD)",
        "Author Royalty (USD)", "Royalty Status", "Comment",
    ]

    FORMAT_DISPLAY = {
        "print": "Print",
        "ebook": "Ebook",
        "kindle unlimited": "Kindle Unlimited",
    }

    @action(detail=False, methods=["get"], url_path="export-csv")
    def export_csv(self, request):
        qs = self.get_queryset()

        now = datetime.now()
        filename = now.strftime("hp-sales-export-%Y-%m-%d-%H%M.csv")

        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        # Write UTF-8 BOM
        response.write("\ufeff")

        writer = csv.writer(response)
        writer.writerow(self.CSV_HEADERS)

        for sale in qs:
            source_display = "Distributor" if sale.sale_source == "distributor" else "Handsold"
            distributor_display = sale.distributor if sale.sale_source == "distributor" and sale.distributor else "N/A"
            format_display = self.FORMAT_DISPLAY.get(sale.format, sale.format or "")

            quantity = str(sale.quantity) if sale.format != "kindle unlimited" and sale.quantity is not None else "N/A"
            kenp = str(sale.kenp) if sale.format == "kindle unlimited" and sale.kenp is not None else "N/A"

            currency = sale.currency or "USD"

            # Pub. Revenue (Original)
            if sale.publisher_revenue_original is not None:
                if currency.upper() in self.ZERO_DECIMAL_CURRENCIES:
                    pub_rev_original = str(int(sale.publisher_revenue_original))
                else:
                    pub_rev_original = f"{sale.publisher_revenue_original:.2f}"
            else:
                pub_rev_original = ""

            # Pub. Revenue (USD) — always 2 decimal places
            pub_rev_usd = f"{sale.publisher_revenue:.2f}" if sale.publisher_revenue is not None else ""

            # Author Royalty (USD) — always 2 decimal places
            royalty_usd = f"{sale.author_royalty:.2f}" if sale.author_royalty is not None else "0.00"

            royalty_status = "Paid" if sale.author_paid else "Unpaid"
            comment = sale.comment or ""

            writer.writerow([
                sale.date.strftime("%Y-%m"),
                sale.book.title,
                sale.book.author.name if sale.book.author else "",
                source_display,
                distributor_display,
                format_display,
                quantity,
                kenp,
                currency,
                pub_rev_original,
                pub_rev_usd,
                royalty_usd,
                royalty_status,
                comment,
            ])

        return response

    # ------------------------------------------------------------------
    # PAY AUTHOR — custom action (marks author_paid=True on this sale)
    # ------------------------------------------------------------------

    @action(detail=True, methods=["post"], url_path="pay-authors")
    def pay_authors(self, request, pk=None):
        sale = self.get_object()

        if sale.author_paid:
            return Response(
                {"detail": "Author already paid for this sale."},
                status=status.HTTP_200_OK,
            )

        with transaction.atomic():
            sale.author_paid = True
            sale.save(update_fields=["author_paid"])

        return Response(
            {
                "sale_id": sale.id,
                "authors_marked_paid": 1,
                "total_royalties_paid": str(sale.author_royalty),
            },
            status=status.HTTP_200_OK,
        )


class BookSalesTotalsView(ModelViewSet):
    """
    Totals endpoint for a single book's sales (for BookDetailPage summary cards).
    Kept as a separate ViewSet since it's book-scoped, not sale-scoped.
    """
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        book_id = kwargs.get("book_pk")

        totals = Sale.objects.filter(book_id=book_id).aggregate(
            publisher_revenue=Coalesce(
                Sum("publisher_revenue"),
                Value(0),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
            total_royalties=Coalesce(
                Sum("author_royalty"),
                Value(0),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
            paid_royalties=Coalesce(
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
            unpaid_royalties=Coalesce(
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
        )

        return Response(
            {
                "book_id": int(book_id),
                "publisher_revenue": str(totals["publisher_revenue"]),
                "total_royalties": str(totals["total_royalties"]),
                "paid_royalties": str(totals["paid_royalties"]),
                "unpaid_royalties": str(totals["unpaid_royalties"]),
            },
            status=status.HTTP_200_OK,
        )