# views/author_payments.py
# Refactored to use ViewSet (Evolution 2: single author per book)

from math import ceil
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Sum, Count, DecimalField, Value
from django.db.models.functions import Coalesce

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from ..models import Author, Sale


DEC2 = Decimal("0.01")
DEC2_FIELD = DecimalField(max_digits=12, decimal_places=2)


def q2(x):
    if x is None:
        x = Decimal("0.00")
    if not isinstance(x, Decimal):
        x = Decimal(str(x))
    return x.quantize(DEC2, rounding=ROUND_HALF_UP)


class AuthorPaymentsViewSet(ViewSet):
    """
    Returns author-grouped payment rows, paginated by AUTHOR.

    Response shape:
    {
      count, page, page_size, total_pages,
      results: [
        {
          author: { id, name },
          unpaidTotal: "12.34",
          unpaidCount: 3,
          rows: [...]
        }
      ]
    }
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        show_all = request.query_params.get("all") in ("1", "true", "True", "yes")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))

        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)

        # Paginate AUTHORS (pagination correctness is purely based on this queryset + slicing)
        author_qs = Author.objects.all().order_by("name", "id")
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

        # Sales rows for these authors (Evolution 2: book has single author FK)
        rows_qs = (
            Sale.objects
            .filter(book__author_id__in=author_ids)
            .select_related("book", "book__author")
            .order_by("-date", "-id")
        )

        # Aggregate unpaid totals/counts keyed by author_id
        unpaid_agg = (
            Sale.objects
            .filter(book__author_id__in=author_ids, author_paid=False)
            .values("book__author_id")
            .annotate(
                unpaid_total=Coalesce(Sum("author_royalty"), Value(0), output_field=DEC2_FIELD),
                unpaid_count=Count("id"),
            )
        )

        unpaid_by_author_id = {
            row["book__author_id"]: row
            for row in unpaid_agg
        }

        groups = {}
        for a in page_authors:
            row = unpaid_by_author_id.get(a.id)
            unpaid_total = q2(row["unpaid_total"]) if row else Decimal("0.00")
            unpaid_count = int(row["unpaid_count"]) if row else 0

            groups[a.id] = {
                "author": {"id": a.id, "name": a.name},
                # return as string to avoid float display rounding issues
                "unpaidTotal": str(unpaid_total),
                "unpaidCount": unpaid_count,
                "rows": [],
            }

        for sale in rows_qs:
            if not sale.book or not sale.book.author_id:
                continue

            aid = sale.book.author_id
            if aid not in groups:
                continue

            author = sale.book.author
            royalty_amt = q2(sale.author_royalty)

            groups[aid]["rows"].append({
                "sale": {
                    "id": sale.id,
                    "book": sale.book_id,
                    "book_title": sale.book.title if sale.book else "",
                    "date": sale.date.strftime("%Y-%m") if sale.date else "",
                    "quantity": sale.quantity,
                    "publisher_revenue": str(q2(sale.publisher_revenue)),
                },
                "author": {
                    "id": author.id,
                    "name": author.name,
                    "royalty_amount": str(royalty_amt),
                    "paid": bool(sale.author_paid),
                },
                "paid": bool(sale.author_paid),
                # return as string to avoid float rounding issues
                "royalty": str(royalty_amt),
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