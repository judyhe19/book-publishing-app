# views/author.py
# Refactored to use ViewSets

from decimal import Decimal

from django.db.models import Sum
from django.db import IntegrityError, transaction

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from ..models import Author, AuthorSale, AuthorBook, Book, Sale
from ..serializers.author import AuthorListSerializer, AuthorCreateSerializer, AuthorUpdateSerializer


class AuthorViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Author.objects.all().order_by("name")

    def get_serializer_class(self):
        if self.action == "create":
            return AuthorCreateSerializer
        if self.action in ["update", "partial_update"]:
            return AuthorUpdateSerializer
        return AuthorListSerializer

    def create(self, request, *args, **kwargs):
        serializer = AuthorCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        name = serializer.validated_data["name"]
        email = serializer.validated_data["email"]

        existing = Author.objects.filter(name__iexact=name).first()
        if existing:
            return Response(AuthorListSerializer(existing).data, status=status.HTTP_200_OK)

        try:
            author = Author.objects.create(name=name, email=email)
        except IntegrityError:
            author = Author.objects.filter(name__iexact=name).first()
            if author:
                return Response(AuthorListSerializer(author).data, status=status.HTTP_200_OK)
            raise

        return Response(AuthorListSerializer(author).data, status=status.HTTP_201_CREATED)
    
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
