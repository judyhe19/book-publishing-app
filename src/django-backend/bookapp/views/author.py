from decimal import Decimal
from django.db.models import Sum
from django.db import IntegrityError
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from ..serializers.author import AuthorListSerializer, AuthorCreateSerializer

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

class AuthorListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        authors = Author.objects.all().order_by("name")
        return Response(AuthorListSerializer(authors, many=True).data)

    def post(self, request):
        serializer = AuthorCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        name = serializer.validated_data["name"]

        # "Create if not exists" behavior (nice for your UX)
        existing = Author.objects.filter(name__iexact=name).first()
        if existing:
            return Response(
                AuthorListSerializer(existing).data,
                status=status.HTTP_200_OK
            )

        try:
            author = Author.objects.create(name=name)
        except IntegrityError:
            # In case of race condition or DB constraint hit
            author = Author.objects.filter(name__iexact=name).first()
            if author:
                return Response(AuthorListSerializer(author).data, status=status.HTTP_200_OK)
            raise

        return Response(AuthorListSerializer(author).data, status=status.HTTP_201_CREATED)
