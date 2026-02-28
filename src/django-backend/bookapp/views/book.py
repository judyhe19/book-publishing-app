# views/book.py
# Refactored to use ModelViewSet (Evolution 2: single author per book)

from django.db.models import Q, OuterRef, Subquery, F, Sum
from django.db.models.functions import Coalesce
from django.db.models import IntegerField

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

        # total_sales_to_date via Subquery (avoids JOIN-multiplication)
        sales_total_sq = (
            Sale.objects.filter(book_id=OuterRef("pk"))
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

            # Search (title, author name, ISBN-13, ISBN-10)
            q = self.request.query_params.get("q")
            if q:
                c_q = q.replace("-", "").strip()
                qs = qs.filter(
                    Q(title__icontains=q)
                    | Q(isbn_13__icontains=c_q)
                    | Q(isbn_10__icontains=c_q)
                    | Q(author__name__icontains=q)
                )

            # Optional filter: published_before
            published_before = self.request.query_params.get("published_before")
            if published_before:
                qs = qs.filter(publication_date__lte=published_before)

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