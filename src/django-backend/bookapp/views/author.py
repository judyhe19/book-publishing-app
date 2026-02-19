# views/author.py
# Refactored to use ViewSets

from decimal import Decimal

from django.db.models import Sum
from django.db import IntegrityError, transaction

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from ..models import Author, AuthorSale
from ..serializers.author import AuthorListSerializer, AuthorCreateSerializer


class AuthorViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Author.objects.all().order_by("name")

    def get_serializer_class(self):
        if self.action == "create":
            return AuthorCreateSerializer
        return AuthorListSerializer

    def create(self, request, *args, **kwargs):
        serializer = AuthorCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        name = serializer.validated_data["name"]
        email = serializer.validated_data["email"]

        # "Create if not exists" behavior
        existing = Author.objects.filter(name__iexact=name).first()
        if existing:
            return Response(
                AuthorListSerializer(existing).data,
                status=status.HTTP_200_OK,
            )

        try:
            author = Author.objects.create(name=name, email=email)
        except IntegrityError:
            # Race condition fallback
            author = Author.objects.filter(name__iexact=name).first()
            if author:
                return Response(AuthorListSerializer(author).data, status=status.HTTP_200_OK)
            raise

        return Response(AuthorListSerializer(author).data, status=status.HTTP_201_CREATED)

    # custom actions
    @action(detail=True, methods=["get"], url_path="unpaid/subtotal")
    def unpaid_subtotal(self, request, pk=None):
        author = self.get_object()

        subtotal = (
            AuthorSale.objects
            .filter(author_id=author.id, author_paid=False)
            .aggregate(total=Sum("royalty_amount"))
            .get("total")
        ) or Decimal("0.00")

        return Response(
            {
                "author_id": author.id,
                "unpaid_subtotal": str(subtotal),
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="pay-unpaid-sales")
    def pay_unpaid_sales(self, request, pk=None):
        author = self.get_object()

        with transaction.atomic():
            qs = (
                AuthorSale.objects
                .select_for_update()
                .filter(author_id=author.id, author_paid=False)
            )

            total_to_pay = qs.aggregate(total=Sum("royalty_amount")).get("total") or Decimal("0.00")

            sale_ids = list(
                AuthorSale.objects
                .filter(author_id=author.id, author_paid=False)
                .values_list("sale_id", flat=True)
                .distinct()
            )

            updated_count = qs.update(author_paid=True)

        return Response(
            {
                "author_id": int(author.id),
                "author_sales_marked_paid": updated_count,
                "total_royalties_paid": str(total_to_pay),
                "sale_ids_affected": sale_ids,
            },
            status=status.HTTP_200_OK,
        )
