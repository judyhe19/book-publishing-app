# views/book.py
# Refactored to use ModelViewSet (Evolution 2: single author per book)

from django.db.models import Q, OuterRef, Subquery, F, Sum, Value
from django.db.models.functions import Coalesce
from django.db.models import IntegerField, DecimalField

# Fields that are nullable and should always sort nulls last
_NULLS_LAST_FIELDS = {"series_name", "series_position", "first_author_name", "first_author_royalty_rate"}

_ALLOWED_ORDER_FIELDS = {
    "title",
    "isbn_13",
    "publication_date",
    "total_sales_to_date",
    "first_author_name",
    "series_name",
    "series_position",
}

_DEFAULT_ORDERING = "first_author_name,series_position,title"


def _parse_ordering(ordering_param):
    """
    Parse a comma-separated ordering string (e.g. "first_author_name,-series_position,title")
    into a list of Django ORM order expressions, with nulls_last on nullable fields.
    Ignores unknown or duplicate fields. Falls back to the default if nothing valid is found.
    Always appends 'id' as the final tiebreaker.
    """
    raw_fields = [f.strip() for f in ordering_param.split(",") if f.strip()]
    seen = set()
    exprs = []
    for raw in raw_fields:
        desc = raw.startswith("-")
        field = raw.lstrip("-")
        if field not in _ALLOWED_ORDER_FIELDS or field in seen:
            continue
        seen.add(field)
        if field in _NULLS_LAST_FIELDS:
            exprs.append(F(field).desc(nulls_last=True) if desc else F(field).asc(nulls_last=True))
        else:
            exprs.append(F(field).desc() if desc else F(field).asc())

    if not exprs:
        exprs = [
            F("first_author_name").asc(nulls_last=True),
            F("series_position").asc(nulls_last=True),
            F("title").asc(),
        ]

    exprs.append(F("id").asc())
    return exprs

from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from ..models import Book, Sale
from ..serializers.book import (
    BookListSerializer,
    BookDetailSerializer,
    BookCreateSerializer,
    BookUpdateSerializer,
    _shift_positions_down,
)
from ..pagination import StandardPagination


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
        """Select author + annotate computed fields."""
        qs = Book.objects.all().select_related("author")

        DEC2 = DecimalField(max_digits=12, decimal_places=2)

        sales_total_sq = (
            Sale.objects.filter(book_id=OuterRef("pk"))
            .values("book_id")
            .annotate(total=Coalesce(Sum("quantity"), Value(0), output_field=IntegerField()))
            .values("total")[:1]
        )

        royalty_total_sq = (
            Sale.objects.filter(book_id=OuterRef("pk"))
            .values("book_id")
            .annotate(total=Coalesce(Sum("author_royalty"), Value(0), output_field=DEC2))
            .values("total")[:1]
        )

        royalty_paid_sq = (
            Sale.objects.filter(book_id=OuterRef("pk"), author_paid=True)
            .values("book_id")
            .annotate(total=Coalesce(Sum("author_royalty"), Value(0), output_field=DEC2))
            .values("total")[:1]
        )

        royalty_unpaid_sq = (
            Sale.objects.filter(book_id=OuterRef("pk"), author_paid=False)
            .values("book_id")
            .annotate(total=Coalesce(Sum("author_royalty"), Value(0), output_field=DEC2))
            .values("total")[:1]
        )

        qs = qs.annotate(
            total_sales_to_date=Coalesce(
                Subquery(sales_total_sq, output_field=IntegerField()),
                Value(0),
                output_field=IntegerField(),
            ),
            total_author_royalty=Coalesce(
                Subquery(royalty_total_sq, output_field=DEC2),
                Value(0),
                output_field=DEC2,
            ),
            paid_author_royalty=Coalesce(
                Subquery(royalty_paid_sq, output_field=DEC2),
                Value(0),
                output_field=DEC2,
            ),
            unpaid_author_royalty=Coalesce(
                Subquery(royalty_unpaid_sq, output_field=DEC2),
                Value(0),
                output_field=DEC2,
            ),
        )

        return qs

    def _annotate_for_sorting(self, qs):
        """
        Add annotations used for sorting.
        Evolution 2: single author lives on Book.author, and the royalty rate
        is Book.distributor_author_royalty_rate.
        """
        return qs.annotate(
            first_author_name=F("author__name"),
            first_author_royalty_rate=F("distributor_author_royalty_rate"),
        )

    # get_queryset (used by list / retrieve)
    def get_queryset(self):
        qs = self._base_queryset()

        # Only add sorting annotations and filters for list action
        if self.action == "list":
            qs = self._annotate_for_sorting(qs)

            author_id = self.request.query_params.get("author_id")
            if author_id:
                qs = qs.filter(author_id=author_id)

            # Search (title, author name, ISBN-13, ISBN-10, Amazon ASIN, Kickstarter tags)
            q = self.request.query_params.get("q")
            if q:
                keywords = q.split()
                for kw in keywords:
                    # Strip dashes for ISBN/ASIN matching
                    c_kw = kw.replace("-", "").strip()
                    qs = qs.filter(
                        Q(title__icontains=kw)
                        | Q(isbn_13__icontains=c_kw)
                        | Q(isbn_10__icontains=c_kw)
                        | Q(amazon_asin_ebook__icontains=c_kw)
                        | Q(author__name__icontains=kw)
                        | Q(series_name__icontains=kw)
                        # Kickstarter tags: exact match (no dash stripping)
                        | Q(kickstarter_item_tag_ebook=kw)
                        | Q(kickstarter_item_tag_print=kw)
                    )

            # Optional filter: published_before
            # Unreleased books are always included (they represent pre-order candidates)
            published_before = self.request.query_params.get("published_before")
            if published_before:
                qs = qs.filter(
                    Q(publication_date__lte=published_before) | Q(released=False)
                )

            # Optional filter: series_name (used by Series Editor page)
            series_filter = self.request.query_params.get("series_name")
            if series_filter:
                qs = qs.filter(series_name=series_filter)

            # Sorting — comma-separated multi-column, e.g. "first_author_name,series_position,title"
            ordering_param = self.request.query_params.get("ordering", _DEFAULT_ORDERING)
            qs = qs.order_by(*_parse_ordering(ordering_param))

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
    # CREATE — return annotated detail
    # ------------------------------------------------------------------

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
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
    # UPDATE (PATCH) — return annotated detail
    # ------------------------------------------------------------------

    def partial_update(self, request, *args, **kwargs):
        book = self.get_object()
        serializer = BookUpdateSerializer(book, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        book = serializer.save()

        book = self._base_queryset().get(pk=book.pk)
        return Response(BookDetailSerializer(book).data)

    # ------------------------------------------------------------------
    # DELETE — cascade-delete sales, then compact series positions
    # ------------------------------------------------------------------

    def destroy(self, request, *args, **kwargs):
        book = self.get_object()
        series_name = book.series_name
        series_position = book.series_position

        with transaction.atomic():
            book.delete()  # CASCADE deletes all related Sales
            if series_name and series_position is not None:
                _shift_positions_down(series_name, series_position)

        return Response(status=status.HTTP_204_NO_CONTENT)