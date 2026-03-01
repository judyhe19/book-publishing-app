# views/author.py
# Refactored to use ViewSets (Evolution 2: single author per book)

from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import (
    Sum, Count, Case, When, Value, Q,
    DecimalField
)
from django.db.models.functions import Coalesce

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from ..models import Author, Book, Sale
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
                qs = qs.filter(Q(name__icontains=q) | Q(email__icontains=q))

            # --- annotations for table columns ---
            # Evolution 2: authored books come from Book.author FK (related_name="books")
            # Royalties are directly on Sale (no AuthorSale table)
            qs = qs.annotate(
                authored_books_count=Count("books", distinct=True),

                total_author_royalty=Coalesce(
                    Sum("books__sales__author_royalty"),
                    Value(0),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),

                paid_author_royalty=Coalesce(
                    Sum(
                        Case(
                            When(books__sales__author_paid=True, then="books__sales__author_royalty"),
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
                            When(books__sales__author_paid=False, then="books__sales__author_royalty"),
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


        try:
            author = Author.objects.create(name=name, email=email)
        except IntegrityError:
            return Response(
                {"name": "An author with this name already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            AuthorListSerializer(author).data,
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        author = self.get_object()
        author_id = author.id

        with transaction.atomic():
            # Evolution 2: books reference author directly via FK
            book_ids = list(
                Book.objects.filter(author_id=author.id)
                .values_list("id", flat=True)
            )

            sale_count = Sale.objects.filter(book_id__in=book_ids).count()

            books_deleted, _ = Book.objects.filter(id__in=book_ids).delete()

            author.delete()

        return Response(
            {
                "author_id": author_id,
                "deleted_book_ids": book_ids,
                "deleted_sales_count": sale_count,
                "books_deleted_objects": books_deleted,
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

        # Query unpaid royalties through Book → Sale (single author FK)
        subtotal = (
            Sale.objects
            .filter(book__author=author, author_paid=False)
            .aggregate(total=Sum("author_royalty"))
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
        DEC2 = DecimalField(max_digits=12, decimal_places=2)

        with transaction.atomic():
            qs = (
                Sale.objects
                .select_for_update()
                .filter(book__author=author, author_paid=False)
            )

            sale_ids = list(qs.values_list("id", flat=True))

            total_to_pay = qs.aggregate(
                total=Coalesce(Sum("author_royalty"), Value(0), output_field=DEC2)
            )["total"] or Decimal("0.00")

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