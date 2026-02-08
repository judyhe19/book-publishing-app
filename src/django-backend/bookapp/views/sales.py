# views/sales.py
# ✅ ONLY functional change: in SaleEditView, if the sale's book changes during edit,
#    rebuild AuthorSale rows from the *new* book's AuthorBook rows.
#    Everything else is unchanged.

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction

from ..models import Sale, Book, AuthorSale, AuthorBook, Author
from ..serializers.sales import SaleSerializer, SaleCreateSerializer

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny

from decimal import Decimal
from django.db.models import (
    Sum,
    Count,
    Case,
    When,
    Value,
    IntegerField,
    Subquery,
    OuterRef,
    DecimalField,
)
from django.db.models.functions import Coalesce

from ..config.sort_config import SALES_SORT_FIELD_MAP, SALES_DEFAULT_SORT
from ..utils import get_first_author_name_subquery

from math import ceil


class SaleGetView(APIView):
    def get(self, request, sale_id=None):
        # If sale_id is provided, return a single sale
        if sale_id is not None:
            sale = get_object_or_404(
                Sale.objects.select_related("book").prefetch_related("author_sales__author"),
                id=sale_id,
            )
            serializer = SaleSerializer(sale)
            return Response(serializer.data)

        book_id = request.query_params.get("book_id")
        user_id = request.query_params.get("user_id")

        queryset = Sale.objects.all()
        queryset = queryset.select_related("book").prefetch_related("author_sales__author")

        if book_id:
            queryset = queryset.filter(book_id=book_id)

        # ✅ keep functional user scoping
        if user_id:
            queryset = queryset.filter(book__publisher_user_id=user_id)

        # Date filtering at month/year granularity
        # Sales are stored by month, so we normalize filter dates to include the whole month
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if start_date:
            parts = start_date.split("-")
            first_of_month = f"{parts[0]}-{parts[1]}-01"
            queryset = queryset.filter(date__gte=first_of_month)

        if end_date:
            import calendar

            parts = end_date.split("-")
            year, month = int(parts[0]), int(parts[1])
            last_day = calendar.monthrange(year, month)[1]
            last_of_month = f"{year}-{month:02d}-{last_day:02d}"
            queryset = queryset.filter(date__lte=last_of_month)

        # annotate with computed fields for sorting
        queryset = queryset.annotate(
            first_author_name=get_first_author_name_subquery("book"),
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

        # server-side ordering
        ordering = request.query_params.get("ordering", SALES_DEFAULT_SORT)
        is_desc = ordering.startswith("-")
        field = ordering[1:] if is_desc else ordering

        if field in SALES_SORT_FIELD_MAP:
            order_field = ("-" if is_desc else "") + SALES_SORT_FIELD_MAP[field]
            queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by("-date")

        # show-all support
        show_all = request.query_params.get("all") in ("1", "true", "True", "yes")
        if show_all:
            total = queryset.count()
            serializer = SaleSerializer(queryset, many=True)
            return Response(
                {
                    "count": total,
                    "page": 1,
                    "page_size": total,
                    "total_pages": 1,
                    "results": serializer.data,
                }
            )

        # pagination params
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 50))
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)

        total = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        page_qs = queryset[start:end]

        serializer = SaleSerializer(page_qs, many=True)

        # ✅ FIX: never return total_pages = 0 (frontend assumes 1-based pages)
        total_pages = max(1, ceil(total / page_size))  # total=0 => 1

        return Response(
            {
                "count": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "results": serializer.data,
            }
        )


# ✅ totals endpoint for a single book (for BookDetailPage summary cards)
class BookSalesTotalsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, book_id):
        qs = Sale.objects.filter(book_id=book_id)

        totals = qs.aggregate(
            publisher_revenue=Coalesce(
                Sum("publisher_revenue"),
                Value(0),
                output_field=DecimalField(),
            ),
            total_royalties=Coalesce(
                Sum("author_sales__royalty_amount"),
                Value(0),
                output_field=DecimalField(),
            ),
            paid_royalties=Coalesce(
                Sum(
                    Case(
                        When(author_sales__author_paid=True, then="author_sales__royalty_amount"),
                        default=Value(0),
                        output_field=DecimalField(),
                    )
                ),
                Value(0),
                output_field=DecimalField(),
            ),
            unpaid_royalties=Coalesce(
                Sum(
                    Case(
                        When(author_sales__author_paid=False, then="author_sales__royalty_amount"),
                        default=Value(0),
                        output_field=DecimalField(),
                    )
                ),
                Value(0),
                output_field=DecimalField(),
            ),
        )

        return Response(
            {
                "book_id": book_id,
                "publisher_revenue": str(totals["publisher_revenue"]),
                "total_royalties": str(totals["total_royalties"]),
                "paid_royalties": str(totals["paid_royalties"]),
                "unpaid_royalties": str(totals["unpaid_royalties"]),
            },
            status=status.HTTP_200_OK,
        )


class SaleCreateView(APIView):
    def post(self, request):
        serializer = SaleCreateSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                sale = serializer.save()

            full_serializer = SaleSerializer(sale)
            return Response(full_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SaleCreateManyView(APIView):
    def post(self, request):
        if not isinstance(request.data, list):
            return Response({"error": "Expected a list of sales"}, status=status.HTTP_400_BAD_REQUEST)

        created_sales = []
        errors = []

        with transaction.atomic():
            for index, sale_data in enumerate(request.data):
                serializer = SaleCreateSerializer(data=sale_data)
                if serializer.is_valid():
                    sale = serializer.save()
                    created_sales.append(sale)
                else:
                    print(f"Validation Error at index {index}: {serializer.errors}")
                    errors.append({"index": index, "errors": serializer.errors})

            if errors:
                transaction.set_rollback(True)
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        full_serializer = SaleSerializer(created_sales, many=True)
        return Response(full_serializer.data, status=status.HTTP_201_CREATED)


class SaleEditView(APIView):
    def post(self, request, sale_id):
        sale = get_object_or_404(Sale, id=sale_id)
        old_quantity = sale.quantity

        # ✅ track old book to detect a book change during edit
        old_book_id = sale.book_id

        fields_param = request.query_params.get("fields")
        partial = True

        data = request.data
        if fields_param:
            allowed_fields = fields_param.split(",")
            data = {k: v for k, v in request.data.items() if k in allowed_fields}

        # ✅ capture possible overrides from the incoming request (if provided)
        #    (keys in these dicts are typically strings)
        incoming_author_royalties = data.get("author_royalties") or {}
        incoming_author_paid = data.get("author_paid") or {}

        serializer = SaleCreateSerializer(sale, data=data, partial=partial)
        if serializer.is_valid():
            with transaction.atomic():
                # ✅ IMPORTANT: do NOT delete author_sales on edit (historical snapshot)
                #    ...EXCEPT when the sale's *book* itself changes: then rebuild AuthorSale rows for the new book.
                updated_sale = serializer.save()

                # ✅ ONLY NEW BEHAVIOR:
                # If the user changed the sale's associated book, reset author_sales
                # to match the current AuthorBook rows for the newly selected book.
                if updated_sale.book_id != old_book_id:
                    # Remove old author allocations (they belong to the previous book)
                    AuthorSale.objects.filter(sale=updated_sale).delete()

                    # Recreate allocations using the new book's current author set
                    author_books = AuthorBook.objects.select_related("author").filter(book=updated_sale.book)

                    for ab in author_books:
                        key = str(ab.author_id)

                        # Override royalty if provided; otherwise compute from current revenue snapshot
                        if key in incoming_author_royalties:
                            royalty_amount = incoming_author_royalties[key]
                        else:
                            royalty_amount = updated_sale.publisher_revenue * ab.royalty_rate

                        author_paid = bool(incoming_author_paid.get(key, False))

                        AuthorSale.objects.create(
                            sale=updated_sale,
                            author=ab.author,
                            royalty_amount=royalty_amount,
                            author_paid=author_paid,
                        )

            full_serializer = SaleSerializer(updated_sale)
            return Response(full_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SaleDeleteView(APIView):
    def delete(self, request, sale_id):
        sale = get_object_or_404(Sale, id=sale_id)
        with transaction.atomic():
            sale.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SalePayAuthorsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, sale_id):
        sale = get_object_or_404(Sale, id=sale_id)

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
