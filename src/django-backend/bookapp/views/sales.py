# views/sales.py
# Refactored to use ModelViewSet

import calendar

from decimal import Decimal, ROUND_HALF_UP
from math import ceil

from django.db import transaction
from django.db.models import (
    Sum, Count, Case, When, Value,
    IntegerField, DecimalField,
)
from django.db.models.functions import Coalesce

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from ..models import Sale, Book
from ..serializers.sales import SaleSerializer, SaleWriteSerializer
from ..config.sort_config import SALES_SORT_FIELD_MAP, SALES_DEFAULT_SORT
from ..pagination import StandardPagination
from ..utils import get_first_author_name_subquery


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
        qs = qs.select_related("book")

        # Filtering (only on list)
        if self.action == "list":
            book_id = self.request.query_params.get("book_id")
            user_id = self.request.query_params.get("user_id")

            if book_id:
                qs = qs.filter(book_id=book_id)
            if user_id:
                qs = qs.filter(book__publisher_user_id=user_id)

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
            qs = qs.annotate(
                first_author_name=get_first_author_name_subquery("book"),
            )

            # Ordering
            ordering = self.request.query_params.get("ordering", SALES_DEFAULT_SORT)
            is_desc = ordering.startswith("-")
            field = ordering[1:] if is_desc else ordering

            if field in SALES_SORT_FIELD_MAP:
                order_field = ("-" if is_desc else "") + SALES_SORT_FIELD_MAP[field]
                qs = qs.order_by(order_field)
            else:
                qs = qs.order_by("-date")

        return qs

    # ------------------------------------------------------------------
    # LIST — uses standard pagination
    # ------------------------------------------------------------------
    # Default ModelViewSet.list() handles pagination via StandardPagination

    # ------------------------------------------------------------------
    # RETRIEVE — single sale by pk
    # ------------------------------------------------------------------
    # Default ModelViewSet.retrieve() handles this

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

    # ------------------------------------------------------------------
    # BOOK SALES TOTALS — custom action on books (routed separately)
    # ------------------------------------------------------------------


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
