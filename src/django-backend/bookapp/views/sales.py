from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from ..models import Sale, Book, AuthorSale, AuthorBook, Author
from ..serializers.sales import SaleSerializer, SaleCreateSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from decimal import Decimal
from django.db.models import Sum

class SaleGetView(APIView):
    def get(self, request):
        book_id = request.query_params.get('book_id')
        user_id = request.query_params.get('user_id')

        queryset = Sale.objects.all()

        if book_id:
            queryset = queryset.filter(book_id=book_id)
        
        # identifying sales by user's published books
        if user_id:
            queryset = queryset.filter(book__publisher_user_id=user_id)

        serializer = SaleSerializer(queryset, many=True)
        return Response(serializer.data)

class SaleCreateView(APIView):
    def post(self, request):
        serializer = SaleCreateSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                sale = serializer.save()
                author_royalties = serializer.validated_data.get('author_royalties', {})
                author_paid = serializer.validated_data.get('author_paid', {})
                sale.create_author_sales(author_royalties, author_paid)
            
            full_serializer = SaleSerializer(sale)
            return Response(full_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class SaleCreateManyView(APIView):
    def post(self, request):
        if not isinstance(request.data, list):
            return Response({"error": "Expected a list of sales"}, status=status.HTTP_400_BAD_REQUEST)
        
        created_sales = []
        errors = []
        
        with transaction.atomic():
            for index, sale_data in enumerate(request.data):
                serializer = SaleCreateSerializer(data=sale_data)
                if serializer.is_valid():
                    sale = serializer.save()
                    author_royalties = serializer.validated_data.get('author_royalties', {})
                    author_paid = serializer.validated_data.get('author_paid', {})
                    sale.create_author_sales(author_royalties, author_paid)
                    created_sales.append(sale)
                else:
                    errors.append({"index": index, "errors": serializer.errors})
            
            if errors:
                # If any fail, we could rollback everything or just report errors. 
                # Identifying best practice: usually bulk create is all or nothing or partial. 
                # Given 'transaction.atomic()', this block will rollback if an exception is raised.
                # However, serializer errors don't raise exceptions by default.
                # Let's decide to rollback if there are any errors for data integrity.
                transaction.set_rollback(True)
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        
        full_serializer = SaleSerializer(created_sales, many=True)
        return Response(full_serializer.data, status=status.HTTP_201_CREATED)

# TODO: frontend needs to send the full state of author_paid and royalties during an edit!!!
class SaleEditView(APIView):
    def post(self, request, sale_id):
        sale = get_object_or_404(Sale, id=sale_id)
        
        fields_param = request.query_params.get('fields')
        partial = True # Always partial update for 'edit' unless specified otherwise

        data = request.data
        if fields_param:
            allowed_fields = fields_param.split(',')
            data = {k: v for k, v in request.data.items() if k in allowed_fields}

        serializer = SaleCreateSerializer(sale, data=data, partial=partial)
        if serializer.is_valid():
            with transaction.atomic():
                updated_sale = serializer.save()
                # If quantity or revenue changed, we might need to recalculate royalties. 
                # Delete old AuthorSales and recreate them.
                sale.author_sales.all().delete()
                author_royalties = serializer.validated_data.get('author_royalties', {})
                author_paid = serializer.validated_data.get('author_paid', {})
                updated_sale.create_author_sales(author_royalties, author_paid)

            full_serializer = SaleSerializer(updated_sale)
            return Response(full_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SaleDeleteView(APIView):
    def delete(self, request, sale_id):
        sale = get_object_or_404(Sale, id=sale_id)
        sale.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SalePayAuthorsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, sale_id):
        sale = get_object_or_404(Sale, id=sale_id)

        with transaction.atomic():
            qs = (
            AuthorSale.objects
            .select_for_update()
            .filter(sale_id=sale.id, author_paid=False)
            )

            total_to_pay = qs.aggregate(total=Sum("royalty_amount")).get("total") or Decimal("0.00")
            updated_count = qs.update(author_paid=True)

        return Response(
        {
        "sale_id": sale.id,
        "authors_marked_paid": updated_count,
        "total_royalties_paid": str(total_to_pay),
        },
        status=status.HTTP_200_OK,
        )
