# views/author_payments.py
# Refactored to use ViewSet

from math import ceil
from decimal import Decimal

from django.db.models import (
    Sum, Count, Case, When, Value, IntegerField, DecimalField,
)
from django.db.models.functions import Coalesce

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from ..models import Author, Sale

# cannot use StandardPagination here because it does not support pagination by author groups (only by individual Sales or Book records)

class AuthorPaymentsViewSet(ViewSet):
    """
    Returns author-grouped payment rows, paginated by AUTHOR.

    Response shape:
    {
      count, page, page_size, total_pages,
      results: [
        {
          author: { id, name },
          unpaidTotal: number,
          unpaidCount: number,
          rows: [...]
        }
      ]
    }
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        # Pagination params
        show_all = request.query_params.get("all") in ("1", "true", "True", "yes")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))

        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)

        # Query authors via Book→AuthorBook relationship,
        # annotating with unpaid sale data from Sale records
        author_qs = (
            Author.objects.all()
            .order_by("name", "id")
            .annotate(
                unpaid_total=Coalesce(
                    Sum(
                        Case(
                            When(
                                books__sales__author_paid=False,
                                then="books__sales__author_royalty",
                            ),
                            default=Value(0),
                            output_field=DecimalField(),
                        )
                    ),
                    Value(0),
                    output_field=DecimalField(),
                ),
                unpaid_count=Count(
                    Case(
                        When(books__sales__author_paid=False, then=1),
                        output_field=IntegerField(),
                    )
                ),
            )
        )

        total_authors = author_qs.count()

        if show_all:
            page_authors = list(author_qs)
            page = 1
            page_size_out = total_authors
            total_pages = 1
        else:
            start = (page - 1) * page_size
            end = start + page_size
            page_authors = list(author_qs[start:end])
            page_size_out = page_size
            total_pages = ceil(total_authors / page_size) if page_size else 0

        author_ids = [a.id for a in page_authors]
        if not author_ids:
            return Response(
                {
                    "count": total_authors,
                    "page": page,
                    "page_size": page_size_out,
                    "total_pages": total_pages,
                    "results": [],
                },
                status=status.HTTP_200_OK,
            )

        # Get sales for these authors via book relationship
        rows_qs = (
            Sale.objects
            .filter(book__authors__id__in=author_ids)
            .select_related("book")
            .prefetch_related("book__authors")
            .order_by("-date", "-id")
        )

        groups = {
            a.id: {
                "author": {"id": a.id, "name": a.name},
                "unpaidTotal": float(a.unpaid_total or Decimal("0.00")),
                "unpaidCount": int(a.unpaid_count or 0),
                "rows": [],
            }
            for a in page_authors
        }

        for sale in rows_qs:
            # Find the author(s) from the book that are in our page_authors set
            for author in sale.book.authors.filter(id__in=author_ids):
                groups[author.id]["rows"].append({
                    "sale": {
                        "id": sale.id,
                        "book": sale.book_id,
                        "book_title": sale.book.title if sale.book else "",
                        "date": sale.date.strftime("%Y-%m") if sale.date else "",
                        "quantity": sale.quantity,
                        "publisher_revenue": str(sale.publisher_revenue),
                    },
                    "author": {
                        "id": author.id,
                        "name": author.name,
                        "royalty_amount": str(sale.author_royalty),
                        "paid": bool(sale.author_paid),
                    },
                    "paid": bool(sale.author_paid),
                    "royalty": float(sale.author_royalty or Decimal("0.00")),
                    "dateKey": sale.date.year * 100 + sale.date.month if sale and sale.date else 0,
                })

        results = [groups[a.id] for a in page_authors]

        return Response(
            {
                "count": total_authors,
                "page": page,
                "page_size": page_size_out,
                "total_pages": total_pages,
                "results": results,
            },
            status=status.HTTP_200_OK,
        )
