# views/author.py
# Refactored to use ViewSets

from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import (
    Sum, Count, Case, When, Value, Q,
    IntegerField, DecimalField
)
from django.db.models.functions import Coalesce


from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from ..models import Author, AuthorSale, AuthorBook, Book, Sale
from ..serializers.author import AuthorListSerializer, AuthorCreateSerializer, AuthorUpdateSerializer
from ..pagination import StandardPagination

AUTHOR_SORT_FIELD_MAP = {
    # displayed columns → queryset fields/annotations
    "name": "name",
    "email": "email",
    "authored_books_count": "authored_books_count",
    "total_author_royalty": "total_author_royalty",
    "paid_author_royalty": "paid_author_royalty",
    "unpaid_author_royalty": "unpaid_author_royalty",
}

AUTHOR_DEFAULT_SORT = "name"

class AuthorViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    queryset = Author.objects.all().order_by("name")

    def get_serializer_class(self):
        if self.action == "create":
            return AuthorCreateSerializer
        if self.action in ["update", "partial_update"]:
            return AuthorUpdateSerializer
        return AuthorListSerializer
    
    def get_queryset(self):
        qs = Author.objects.all()

        # Only annotate/filter/sort for list endpoint
        if self.action == "list":
            # --- keyword search (name + email) ---
            q = (self.request.query_params.get("q") or "").strip()
            if q:
                qs = qs.filter(
                    Q(name__icontains=q) | Q(email__icontains=q)
                )

            # --- annotations for table columns ---
            qs = qs.annotate(
                authored_books_count=Count("authorbook_set__book", distinct=True),

                total_author_royalty=Coalesce(
                    Sum("sales_records__royalty_amount"),
                    Value(0),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),

                paid_author_royalty=Coalesce(
                    Sum(
                        Case(
                            When(sales_records__author_paid=True, then="sales_records__royalty_amount"),
                            default=Value(0),
                            output_field=DecimalField(max_digits=12, decimal_places=2),
                        )
                    ),
                    Value(0),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),

                unpaid_author_royalty=Coalesce(
                    Sum(
                        Case(
                            When(sales_records__author_paid=False, then="sales_records__royalty_amount"),
                            default=Value(0),
                            output_field=DecimalField(max_digits=12, decimal_places=2),
                        )
                    ),
                    Value(0),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
            )

            # --- ordering ---
            ordering = self.request.query_params.get("ordering", AUTHOR_DEFAULT_SORT)
            is_desc = ordering.startswith("-")
            field = ordering[1:] if is_desc else ordering

            mapped = AUTHOR_SORT_FIELD_MAP.get(field, AUTHOR_DEFAULT_SORT)
            order_field = ("-" if is_desc else "") + mapped

            # stable secondary sort by id to reduce jitter across pages
            qs = qs.order_by(order_field, "id")

        else:
            # for retrieve/update/destroy keep simple ordering
            qs = qs.order_by("name")

        return qs

    def create(self, request, *args, **kwargs):
        serializer = AuthorCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        name = serializer.validated_data["name"]
        email = serializer.validated_data["email"]

        # Email must be unique
        if Author.objects.filter(email__iexact=email).exists():
            return Response(
                {"email": "An author with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            author = Author.objects.create(name=name, email=email)
        except IntegrityError:
            return Response(
                {"email": "An author with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            AuthorListSerializer(author).data,
            status=status.HTTP_201_CREATED,
        )
    
    def destroy(self, request, *args, **kwargs):
        author = self.get_object()

        with transaction.atomic():
            book_ids = list(
                AuthorBook.objects.filter(author_id=author.id)
                .values_list("book_id", flat=True)
                .distinct()
            )

            sale_count = Sale.objects.filter(book_id__in=book_ids).count()

            books_deleted, _ = Book.objects.filter(id__in=book_ids).delete()

            author.delete()

        return Response(
            {
                "author_id": int(author.id),
                "deleted_book_ids": book_ids,
                "deleted_sales_count": int(sale_count),
                "books_deleted_objects": int(books_deleted),
            },
            status=status.HTTP_200_OK,
        )
    
    def update(self, request, *args, **kwargs):
        # Handles PUT
        author = self.get_object()
        serializer = AuthorUpdateSerializer(author, data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            author = serializer.save()
        except IntegrityError:
            return Response(
                {"detail": "Author with that name or email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(AuthorListSerializer(author).data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        # Handles PATCH
        author = self.get_object()
        serializer = AuthorUpdateSerializer(author, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            author = serializer.save()
        except IntegrityError:
            return Response(
                {"detail": "Author with that name or email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(AuthorListSerializer(author).data, status=status.HTTP_200_OK)

    # custom actions
    @action(detail=True, methods=["get"], url_path="unpaid/subtotal")
    def unpaid_subtotal(self, request, pk=None):
        author = self.get_object()

        subtotal = (
            AuthorSale.objects
            .filter(author_id=author.id, author_paid=False)
            .aggregate(total=Sum("royalty_amount"))
            .get("total")
        ) or Decimal("0.00")

        return Response(
            {
                "author_id": author.id,
                "unpaid_subtotal": str(subtotal),
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="pay-unpaid-sales")
    def pay_unpaid_sales(self, request, pk=None):
        author = self.get_object()

        with transaction.atomic():
            qs = (
                AuthorSale.objects
                .select_for_update()
                .filter(author_id=author.id, author_paid=False)
            )

            total_to_pay = qs.aggregate(total=Sum("royalty_amount")).get("total") or Decimal("0.00")

            sale_ids = list(
                AuthorSale.objects
                .filter(author_id=author.id, author_paid=False)
                .values_list("sale_id", flat=True)
                .distinct()
            )

            updated_count = qs.update(author_paid=True)

        return Response(
            {
                "author_id": int(author.id),
                "author_sales_marked_paid": updated_count,
                "total_royalties_paid": str(total_to_pay),
                "sale_ids_affected": sale_ids,
            },
            status=status.HTTP_200_OK,
        )
