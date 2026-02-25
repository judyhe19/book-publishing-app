# views/sales.py
# Refactored to use ModelViewSet (Evolution 2: single author per book)

import calendar
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import (
    Sum, Count, Case, When, Value,
    IntegerField, DecimalField, F,
)
from django.db.models.functions import Coalesce

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from ..models import Sale, AuthorSale
from ..serializers.sales import SaleSerializer, SaleWriteSerializer
from ..config.sort_config import SALES_SORT_FIELD_MAP, SALES_DEFAULT_SORT
from ..pagination import StandardPagination


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
        qs = qs.select_related("book", "book__author").prefetch_related("author_sales__author")

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
            # Evolution 2: single author on Book; royalties use distributor_author_royalty_rate at time of sale creation
            qs = qs.annotate(
                first_author_name=F("book__author__name"),
                total_royalties=Sum("author_sales__royalty_amount"),
                unpaid_count=Count(
                    Case(
                        When(author_sales__author_paid=False, then=1),
                        output_field=IntegerField(),
                    )
                ),
                paid_count=Count(
                    Case(
                        When(author_sales__author_paid=True, then=1),
                        output_field=IntegerField(),
                    )
                ),
                total_author_count=Count("author_sales"),
                paid_status_order=Case(
                    When(unpaid_count=0, total_author_count__gt=0, then=Value(0)),
                    When(paid_count__gt=0, unpaid_count__gt=0, then=Value(1)),
                    default=Value(2),
                    output_field=IntegerField(),
                ),
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
        old_book_id = sale.book_id

        fields_param = request.query_params.get("fields")
        data = request.data
        if fields_param:
            allowed_fields = fields_param.split(",")
            data = {k: v for k, v in request.data.items() if k in allowed_fields}

        incoming_author_royalties = data.get("author_royalties") or {}
        incoming_author_paid = data.get("author_paid") or {}

        serializer = SaleWriteSerializer(sale, data=data, partial=True)
        if serializer.is_valid():
            with transaction.atomic():
                updated_sale = serializer.save()

                # If book changed, rebuild AuthorSale rows (Evolution 2: exactly one author)
                if updated_sale.book_id != old_book_id:
                    AuthorSale.objects.filter(sale=updated_sale).delete()

                    author = updated_sale.book.author
                    key = str(author.id)

                    if key in incoming_author_royalties:
                        royalty_amount = money(incoming_author_royalties[key])
                    else:
                        royalty_amount = money(
                            updated_sale.publisher_revenue * updated_sale.book.distributor_author_royalty_rate
                        )

                    author_paid = bool(incoming_author_paid.get(key, False))

                    AuthorSale.objects.create(
                        sale=updated_sale,
                        author=author,
                        royalty_amount=royalty_amount,
                        author_paid=author_paid,
                    )

            full_serializer = SaleSerializer(updated_sale)
            return Response(full_serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Also support PUT as same behavior as PATCH
    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.partial_update(request, *args, **kwargs)

    # ------------------------------------------------------------------
    # PAY AUTHORS — custom action
    # ------------------------------------------------------------------

    @action(detail=True, methods=["post"], url_path="pay-authors")
    def pay_authors(self, request, pk=None):
        sale = self.get_object()

        with transaction.atomic():
            qs = (
                AuthorSale.objects.select_for_update()
                .filter(sale_id=sale.id, author_paid=False)
            )
            total_to_pay = qs.aggregate(total=Sum("royalty_amount")).get("total") or Decimal("0.00")
            updated_count = qs.update(author_paid=True)

        return Response(
            {
                "sale_id": sale.id,
                "authors_marked_paid": updated_count,
                "total_royalties_paid": str(total_to_pay),
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

        publisher_revenue = Sale.objects.filter(book_id=book_id).aggregate(
            total=Coalesce(
                Sum("publisher_revenue"),
                Value(0),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )["total"]

        royalty_totals = AuthorSale.objects.filter(sale__book_id=book_id).aggregate(
            total_royalties=Coalesce(
                Sum("royalty_amount"),
                Value(0),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
            paid_royalties=Coalesce(
                Sum(
                    Case(
                        When(author_paid=True, then="royalty_amount"),
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
                        When(author_paid=False, then="royalty_amount"),
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
                "publisher_revenue": str(publisher_revenue),
                "total_royalties": str(royalty_totals["total_royalties"]),
                "paid_royalties": str(royalty_totals["paid_royalties"]),
                "unpaid_royalties": str(royalty_totals["unpaid_royalties"]),
            },
            status=status.HTTP_200_OK,
        )