# views/books.py
# User-agnostic: removes all dependencies on request.user and publisher_user

from math import ceil

from django.db.models import Q, Prefetch
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Book, AuthorBook
from ..serializers.book import (
    BookListSerializer,
    BookDetailSerializer,
    BookCreateSerializer,
    BookUpdateSerializer,
)


class BookListCreateView(APIView):
    # Keep auth if you still want only logged-in users to access the API.
    # If you truly want public access, replace with AllowAny.
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # --------------------
        # Query params
        # --------------------
        fields = request.query_params.get("fields")  # optional; safe to keep
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 50))
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
                    queryset=AuthorBook.objects.select_related("author").order_by("author__name", "author_id"),
                )
            )
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
        # Note: author(s) and royalty_rate sorting requires a defined rule.
        # --------------------
        allowed_order_fields = {
            "title",
            "isbn_13",
            "isbn_10",
            "publication_date",
            "total_sales_to_date",
            "id",
        }

        sort_field = ordering
        desc = False
        if sort_field.startswith("-"):
            desc = True
            sort_field = sort_field[1:]

        if sort_field not in allowed_order_fields:
            sort_field = "title"
            desc = False

        order_by = f"-{sort_field}" if desc else sort_field

        # Stable tiebreaker for pagination
        qs = qs.order_by(order_by, "id")

        # --------------------
        # Pagination
        # --------------------
        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size
        books = qs[start:end]

        data = BookListSerializer(books, many=True).data

        # Optional: fields filtering
        # (Be careful not to remove fields your frontend needs, like "authors".)
        if fields:
            wanted = {f.strip() for f in fields.split(",")}
            data = [{k: v for k, v in item.items() if k in wanted} for item in data]

        return Response({
            "count": total,
            "page": page,
            "page_size": page_size,
            "total_pages": ceil(total / page_size) if page_size else 0,
            "results": data,
        })

    def post(self, request):
        serializer = BookCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        # No user-based ownership
        book = serializer.save()

        # Return read-shape (consistent with list/detail)
        return Response(
            BookDetailSerializer(book).data,
            status=status.HTTP_201_CREATED
        )


class BookDetailView(APIView):
    # Keep auth if you still want only logged-in users to access the API.
    # If you truly want public access, replace with AllowAny.
    permission_classes = [IsAuthenticated]

    def get(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)

        # Prefetch authors for consistent detail response
        book = (
            Book.objects
            .filter(id=book.id)
            .prefetch_related(
                Prefetch(
                    "authorbook_set",
                    queryset=AuthorBook.objects.select_related("author").order_by("author__name", "author_id"),
                )
            )
            .first()
        )

        return Response(BookDetailSerializer(book).data)

    def patch(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)

        serializer = BookUpdateSerializer(book, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        book = serializer.save()

        # Re-fetch with prefetch for nested output consistency
        book = (
            Book.objects
            .filter(id=book.id)
            .prefetch_related(
                Prefetch(
                    "authorbook_set",
                    queryset=AuthorBook.objects.select_related("author").order_by("author__name", "author_id"),
                )
            )
            .first()
        )

        return Response(BookDetailSerializer(book).data)

    def delete(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        book.delete()
        return Response(status=204)
