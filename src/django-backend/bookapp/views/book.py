# views/books.py
# User-agnostic: removes all dependencies on request.user and publisher_user

from math import ceil

from django.db import transaction
from django.db.models import Q, Prefetch, OuterRef, Subquery, F
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.db.models import IntegerField

from ..models import Book, AuthorBook, Sale  # ✅ CHANGED: import Sale for subquery totals
from ..serializers.book import (
    BookListSerializer,
    BookDetailSerializer,
    BookCreateSerializer,
    BookUpdateSerializer,
)

from ..utils import get_first_author_name_subquery


class BookListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # --------------------
        # Query params
        # --------------------
        fields = request.query_params.get("fields")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 50))
        show_all = request.query_params.get("all") in ("1", "true", "True", "yes")
        ordering = request.query_params.get("ordering", "title")
        q = request.query_params.get("q")
        published_before = request.query_params.get("published_before")

        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)

        # --------------------
        # Base queryset (NO user scoping)
        # Prefetch through table + author for efficient nested output
        # --------------------
        qs = (
            Book.objects
            .all()
            .prefetch_related(
                Prefetch(
                    "authorbook_set",
                    queryset=AuthorBook.objects.select_related("author").order_by("author_id"),
                )
            )
        )

        # --------------------
        # ✅ total_sales_to_date computed from Sale.quantity (no stored counter)
        #
        # IMPORTANT: compute via Subquery to avoid JOIN-multiplication when search joins authors
        # (this prevents "doubling" totals when q matches author name)
        # --------------------
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

        # --------------------
        # Annotations for sorting by "first author" and "first royalty rate"
        # First author is defined as the AuthorBook row with the smallest author_id.
        # --------------------
        first_ab = (
            AuthorBook.objects
            .filter(book_id=OuterRef("pk"))
            .order_by("author_id")
        )

        qs = qs.annotate(
            first_author_name=get_first_author_name_subquery("pk"),
            first_author_royalty_rate=Subquery(first_ab.values("royalty_rate")[:1]),
        )

        # --------------------
        # Search (title, author name, ISBN-13, ISBN-10)
        # --------------------
        if q:
            c_q = q.replace("-", "").strip()
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(isbn_13__icontains=c_q) |
                Q(isbn_10__icontains=c_q) |
                Q(authors__name__icontains=q)
            ).distinct()

        # --------------------
        # Optional filter: published_before
        # --------------------
        if published_before:
            qs = qs.filter(publication_date__lte=published_before)

        # --------------------
        # Sorting (backend)
        # --------------------
        allowed_order_fields = {
            "title",
            "isbn_13",
            "isbn_10",
            "publication_date",
            "total_sales_to_date",
            "id",
            "first_author_name",
            "first_author_royalty_rate",
        }

        sort_field = ordering
        desc = False
        if sort_field.startswith("-"):
            desc = True
            sort_field = sort_field[1:]

        if sort_field not in allowed_order_fields:
            sort_field = "title"
            desc = False

        # Postgres: put NULLs last for the annotated fields (books with no authors)
        if sort_field in {"first_author_name", "first_author_royalty_rate"}:
            sort_expr = F(sort_field).desc(nulls_last=True) if desc else F(sort_field).asc(nulls_last=True)
            qs = qs.order_by(sort_expr, "id")
        else:
            order_by = f"-{sort_field}" if desc else sort_field
            qs = qs.order_by(order_by, "id")

        # --------------------
        # Pagination
        # --------------------
        total = qs.count()

        if show_all:
            books = qs
            data = BookListSerializer(books, many=True).data

            if fields:
                wanted = {f.strip() for f in fields.split(",")}
                data = [{k: v for k, v in item.items() if k in wanted} for item in data]

            return Response({
                "count": total,
                "page": 1,
                "page_size": total,
                "total_pages": 1,
                "results": data,
            })

        start = (page - 1) * page_size
        end = start + page_size
        books = qs[start:end]

        data = BookListSerializer(books, many=True).data

        if fields:
            wanted = {f.strip() for f in fields.split(",")}
            data = [{k: v for k, v in item.items() if k in wanted} for item in data]

        return Response({
            "count": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, ceil(total / page_size)),
            "results": data,
        })

    def post(self, request):
        serializer = BookCreateSerializer(data=request.data)

        # ✅ Atomic: if anything fails (validation or DB), nothing is written (including new Authors)
        with transaction.atomic():
            serializer.is_valid(raise_exception=True)
            book = serializer.save()

        return Response(
            BookDetailSerializer(book).data,
            status=status.HTTP_201_CREATED
        )


class BookDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)

        book = (
            Book.objects
            .filter(id=book.id)
            .annotate(
                total_sales_to_date=Coalesce(
                    Sum("sales__quantity"),
                    0,
                    output_field=IntegerField(),
                )
            )
            .prefetch_related(
                Prefetch(
                    "authorbook_set",
                    queryset=AuthorBook.objects.select_related("author").order_by("author_id"),
                )
            )
            .first()
        )

        return Response(BookDetailSerializer(book).data)

    def patch(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)

        serializer = BookUpdateSerializer(book, data=request.data, partial=True)

        # ✅ Atomic: if PATCH includes new authors (by name) and anything fails, no new Authors persist.
        with transaction.atomic():
            serializer.is_valid(raise_exception=True)
            book = serializer.save()

        book = (
            Book.objects
            .filter(id=book.id)
            .annotate(
                total_sales_to_date=Coalesce(
                    Sum("sales__quantity"),
                    0,
                    output_field=IntegerField(),
                )
            )
            .prefetch_related(
                Prefetch(
                    "authorbook_set",
                    queryset=AuthorBook.objects.select_related("author").order_by("author_id"),
                )
            )
            .first()
        )

        return Response(BookDetailSerializer(book).data)

    def delete(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        book.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
