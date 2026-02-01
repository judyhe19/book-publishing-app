from decimal import Decimal
from django.db.models import Sum
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from ..models import Author, AuthorSale


class AuthorUnpaidSubtotalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, author_id):
        get_object_or_404(Author, id=author_id)

        subtotal = (
            AuthorSale.objects
            .filter(author_id=author_id, author_paid=False)
            .aggregate(total=Sum("royalty_amount"))
            .get("total")
        ) or Decimal("0.00")

        return Response(
            {
                "author_id": author_id,
                "unpaid_subtotal": str(subtotal),
            },
            status=status.HTTP_200_OK,
        )

class AuthorPayUnpaidSalesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, author_id):
        get_object_or_404(Author, id=author_id)

        with transaction.atomic():
            qs = (
                 AuthorSale.objects
                 .select_for_update()
                 .filter(author_id=author_id, author_paid=False)
             )


            total_to_pay = qs.aggregate(total=Sum("royalty_amount")).get("total") or Decimal("0.00")

            sale_ids = list(
               AuthorSale.objects
                .filter(author_id=author_id, author_paid=False)
                .values_list("sale_id", flat=True)
                .distinct()
            )

            updated_count = qs.update(author_paid=True)

        return Response(
            {
                "author_id": int(author_id),
                "author_sales_marked_paid": updated_count,
                "total_royalties_paid": str(total_to_pay),
                "sale_ids_affected": sale_ids,
            },
            status=status.HTTP_200_OK,
        )
