from math import ceil
from decimal import Decimal

from django.db.models import (
    Sum, Count, Case, When, Value, IntegerField, DecimalField
)
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from ..models import Author, AuthorSale


class AuthorPaymentsGroupedView(APIView):
    """
    Returns author-grouped payment rows, paginated by AUTHOR.

    Response shape mirrors what your frontend expects:
    {
      count, page, page_size, total_pages,
      results: [
        {
          author: { id, name },
          unpaidTotal: number,
          unpaidCount: number,
          rows: [
            { sale: <SaleSerializer-like fields>, author: <author_details row>, paid, royalty, dateKey }
          ]
        }
      ]
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # pagination params
        show_all = request.query_params.get("all") in ("1", "true", "True", "yes")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))

        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)

        # default (and only) ordering per your spec: author name asc
        # (keeping ordering param out for now intentionally)
        author_qs = (
            Author.objects
            .all()
            .order_by("name", "id")
            .annotate(
                unpaid_total=Coalesce(
                    Sum(
                        Case(
                            # FIX: authorsale__... -> sales_records__...
                            When(sales_records__author_paid=False, then="sales_records__royalty_amount"),
                            default=Value(0),
                            output_field=DecimalField(),
                        )
                    ),
                    Value(0),
                    output_field=DecimalField(),
                ),
                unpaid_count=Count(
                    Case(
                        # FIX: authorsale__... -> sales_records__...
                        When(sales_records__author_paid=False, then=1),
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

        # Fetch all AuthorSale rows for authors on THIS page.
        # This bounds queries unless user hits "Show all".
        rows_qs = (
            AuthorSale.objects
            .filter(author_id__in=author_ids)
            .select_related("author", "sale", "sale__book")
            .order_by("author__name", "-sale__date", "-sale__id")
        )

        # Build groups in the same order as author_qs pagination returned
        author_by_id = {a.id: a for a in page_authors}
        groups = {a.id: {
            "author": {"id": a.id, "name": a.name},
            "unpaidTotal": float(a.unpaid_total or Decimal("0.00")),
            "unpaidCount": int(a.unpaid_count or 0),
            "rows": [],
        } for a in page_authors}

        for ars in rows_qs:
            sale = ars.sale
            # shape matches your frontend rows: { sale, author, paid, royalty, dateKey }
            groups[ars.author_id]["rows"].append({
                "sale": {
                    "id": sale.id,
                    "book": sale.book_id,
                    "book_title": sale.book.title if sale.book else "",
                    "date": str(sale.date),
                    "quantity": sale.quantity,
                    "publisher_revenue": str(sale.publisher_revenue),
                },
                "author": {
                    "id": ars.author_id,
                    "name": ars.author.name if ars.author else "",
                    "royalty_amount": str(ars.royalty_amount),
                    "paid": bool(ars.author_paid),
                },
                "paid": bool(ars.author_paid),
                "royalty": float(ars.royalty_amount or Decimal("0.00")),
                "dateKey": int(sale.date.strftime("%s")) if sale and sale.date else 0,
            })

        # Ensure author order is preserved
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
