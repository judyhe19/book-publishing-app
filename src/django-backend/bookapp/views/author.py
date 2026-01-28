from decimal import Decimal
from django.db.models import Sum
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