# views/book.py
# Refactored to use ModelViewSet

from django.db import transaction
from django.db.models import Q, Prefetch, OuterRef, Subquery, F, Sum
from django.db.models.functions import Coalesce
from django.db.models import IntegerField

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from ..models import Book, AuthorBook, Sale
from ..serializers.book import (
    BookListSerializer,
    BookDetailSerializer,
    BookCreateSerializer,
    BookUpdateSerializer,
)
from ..pagination import StandardPagination
from ..utils import get_first_author_name_subquery


class BookViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    lookup_field = "pk"

    def get_serializer_class(self):
        if self.action == "create":
            return BookCreateSerializer
        if self.action in ("update", "partial_update"):
            return BookUpdateSerializer
        if self.action == "retrieve":
            return BookDetailSerializer
        return BookListSerializer

    # ------------------------------------------------------------------
    # Shared queryset building
    # ------------------------------------------------------------------

    def _base_queryset(self):
        """Prefetch authors + annotate computed fields."""
        qs = (
            Book.objects.all()
            .prefetch_related(
                Prefetch(
                    "authorbook_set",
                    queryset=AuthorBook.objects.select_related("author").order_by("author_id"),
                )
            )
        )

        # total_sales_to_date via Subquery (avoids JOIN-multiplication)
        sales_total_sq = (
            Sale.objects
            .filter(book_id=OuterRef("pk"))
            .values("book_id")
            .annotate(total=Coalesce(Sum("quantity"), 0))
            .values("total")[:1]
        )

        qs = qs.annotate(
            total_sales_to_date=Coalesce(
                Subquery(sales_total_sq, output_field=IntegerField()),
                0,
                output_field=IntegerField(),
            )
        )

        return qs

    def _annotate_for_sorting(self, qs):
        """Add first-author annotations used for sorting."""
        first_ab = (
            AuthorBook.objects
            .filter(book_id=OuterRef("pk")) # pk = primary key of the book (outer query primary key)
            .order_by("author_id")
        )

        qs = qs.annotate(
            first_author_name=get_first_author_name_subquery("pk"), 
            first_author_royalty_rate=Subquery(first_ab.values("royalty_rate")[:1]),
        )
        return qs

    # ------------------------------------------------------------------
    # get_queryset (used by list / retrieve)
    # ------------------------------------------------------------------

    def get_queryset(self):
        qs = self._base_queryset()

        # Only add sorting annotations and filters for list action
        if self.action == "list":
            qs = self._annotate_for_sorting(qs)

            # Search (title, author name, ISBN-13, ISBN-10)
            q = self.request.query_params.get("q")
            if q:
                c_q = q.replace("-", "").strip()
                qs = qs.filter(
                    Q(title__icontains=q)
                    | Q(isbn_13__icontains=c_q)
                    | Q(isbn_10__icontains=c_q)
                    | Q(authors__name__icontains=q)
                ).distinct()

            # Optional filter: published_before
            published_before = self.request.query_params.get("published_before")
            if published_before:
                qs = qs.filter(publication_date__lte=published_before)

            # Sorting
            ordering = self.request.query_params.get("ordering", "title")
            allowed_order_fields = {
                "title", "isbn_13", "isbn_10", "publication_date",
                "total_sales_to_date", "id",
                "first_author_name", "first_author_royalty_rate",
            }

            sort_field = ordering
            desc = False
            if sort_field.startswith("-"):
                desc = True
                sort_field = sort_field[1:]

            if sort_field not in allowed_order_fields:
                sort_field = "title"
                desc = False

            if sort_field in {"first_author_name", "first_author_royalty_rate"}:
                sort_expr = F(sort_field).desc(nulls_last=True) if desc else F(sort_field).asc(nulls_last=True)
                qs = qs.order_by(sort_expr, "id")
            else:
                order_by = f"-{sort_field}" if desc else sort_field
                qs = qs.order_by(order_by, "id")

        return qs

    # ------------------------------------------------------------------
    # LIST  — override to support ?fields= sparse fieldsets
    # ------------------------------------------------------------------

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = self._apply_fields_filter(request, serializer.data)
            return self.get_paginated_response(data)

        serializer = self.get_serializer(queryset, many=True)
        data = self._apply_fields_filter(request, serializer.data)
        return Response(data)

    def _apply_fields_filter(self, request, data):
        """Support ?fields=title,isbn_13 sparse fieldsets."""
        fields = request.query_params.get("fields")
        if fields:
            wanted = {f.strip() for f in fields.split(",")}
            data = [{k: v for k, v in item.items() if k in wanted} for item in data]
        return data

    # ------------------------------------------------------------------
    # CREATE — wrap in transaction
    # ------------------------------------------------------------------

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        with transaction.atomic():
            serializer.is_valid(raise_exception=True)
            book = serializer.save()

        # Return detail representation (with annotations)
        book = self._base_queryset().get(pk=book.pk)
        return Response(
            BookDetailSerializer(book).data,
            status=status.HTTP_201_CREATED,
        )

    # ------------------------------------------------------------------
    # RETRIEVE — use annotated queryset
    # ------------------------------------------------------------------

    def retrieve(self, request, *args, **kwargs):
        book = self._base_queryset().get(pk=self.get_object().pk)
        return Response(BookDetailSerializer(book).data)

    # ------------------------------------------------------------------
    # UPDATE (PATCH) — wrap in transaction, return annotated detail
    # ------------------------------------------------------------------

    def partial_update(self, request, *args, **kwargs):
        book = self.get_object()
        serializer = BookUpdateSerializer(book, data=request.data, partial=True)

        with transaction.atomic():
            serializer.is_valid(raise_exception=True)
            book = serializer.save()

        book = self._base_queryset().get(pk=book.pk)
        return Response(BookDetailSerializer(book).data)
