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
from django.db.models import Sum, Count, Case, When, Value, IntegerField, Subquery, OuterRef
from ..config.sort_config import SALES_SORT_FIELD_MAP, SALES_DEFAULT_SORT


class SaleGetView(APIView):
    def get(self, request, sale_id=None):
        # If sale_id is provided, return a single sale
        if sale_id is not None:
            sale = get_object_or_404(Sale, id=sale_id)
            serializer = SaleSerializer(sale)
            return Response(serializer.data)
        
        book_id = request.query_params.get('book_id')
        user_id = request.query_params.get('user_id')

        queryset = Sale.objects.all()

        if book_id:
            queryset = queryset.filter(book_id=book_id)
        
        # identifying sales by user's published books
        if user_id:
            queryset = queryset.filter(book__publisher_user_id=user_id)

        # Date filtering at month/year granularity
        # Sales are stored by month, so we normalize filter dates to include the whole month
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            # Use first day of the start date's month
            from datetime import date
            parts = start_date.split('-')
            first_of_month = f"{parts[0]}-{parts[1]}-01"
            queryset = queryset.filter(date__gte=first_of_month)
        if end_date:
            # Use last day of the end date's month
            from datetime import date
            import calendar
            parts = end_date.split('-')
            year, month = int(parts[0]), int(parts[1])
            last_day = calendar.monthrange(year, month)[1]
            last_of_month = f"{year}-{month:02d}-{last_day:02d}"
            queryset = queryset.filter(date__lte=last_of_month)
        
        # subquery to get the first author's name for this sale's book
        first_author_subquery = Author.objects.filter(
            authorbook__book=OuterRef('book')
        ).order_by('authorbook__id').values('name')[:1]
        
        # annotate with computed fields for sorting: total_royalties, unpaid_count, paid_count, total_author_count, and first_author_name
        queryset = queryset.annotate(
            # first author's name for sorting
            first_author_name=Subquery(first_author_subquery),
            # total royalties for this sale (sum of all author royalties)
            total_royalties=Sum('author_sales__royalty_amount'),
            # count of unpaid authors (0 means all paid)
            unpaid_count=Count(
                Case(
                    When(author_sales__author_paid=False, then=1),
                    output_field=IntegerField()
                )
            ),
            # count of paid authors (for partial payment detection)
            paid_count=Count(
                Case(
                    When(author_sales__author_paid=True, then=1),
                    output_field=IntegerField()
                )
            ),
            # total author count for this sale
            total_author_count=Count('author_sales'),
            # paid_status_order: 0=Fully Paid, 1=Partially Paid, 2=Unpaid
            # Using Case/When to create a sortable status field
            paid_status_order=Case(
                # Fully Paid: unpaid_count = 0 AND total_author_count > 0
                When(unpaid_count=0, total_author_count__gt=0, then=Value(0)),
                # Partially Paid: paid_count > 0 AND unpaid_count > 0
                When(paid_count__gt=0, unpaid_count__gt=0, then=Value(1)),
                # Unpaid: paid_count = 0 (or no authors at all)
                default=Value(2),
                output_field=IntegerField()
            )
        )
        
        # server-side ordering
        ordering = request.query_params.get('ordering', SALES_DEFAULT_SORT)

        # parse ordering (handle descending prefix)
        is_desc = ordering.startswith('-')
        field = ordering[1:] if is_desc else ordering
        
        if field in SALES_SORT_FIELD_MAP:
            order_field = ('-' if is_desc else '') + SALES_SORT_FIELD_MAP[field]
            queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by('-date')  # fallback to default if invalid field was passed in

        serializer = SaleSerializer(queryset, many=True)
        return Response(serializer.data)

class SaleCreateView(APIView):
    def post(self, request):
        serializer = SaleCreateSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                sale = serializer.save()
                sale.book.update_total_sales(sale.quantity)
            
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
                    sale.book.update_total_sales(sale.quantity)
                    created_sales.append(sale)
                else:
                    print(f"Validation Error at index {index}: {serializer.errors}")
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
        old_quantity = sale.quantity
        
        fields_param = request.query_params.get('fields')
        partial = True # Always partial update for 'edit' unless specified otherwise

        data = request.data
        if fields_param:
            allowed_fields = fields_param.split(',')
            data = {k: v for k, v in request.data.items() if k in allowed_fields}

        serializer = SaleCreateSerializer(sale, data=data, partial=partial) # calls update() if sale is passed in
        if serializer.is_valid():
            with transaction.atomic():
                # If quantity or revenue changed, we might need to recalculate royalties. 
                # Delete old AuthorSales and recreate them when call serializer.save()
                sale.author_sales.all().delete()
                updated_sale = serializer.save()
                
                # Update book's total_sales_to_date if quantity changed
                quantity_diff = updated_sale.quantity - old_quantity
                if quantity_diff != 0:
                    updated_sale.book.update_total_sales(quantity_diff)

            full_serializer = SaleSerializer(updated_sale)
            return Response(full_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SaleDeleteView(APIView):
    def delete(self, request, sale_id):
        sale = get_object_or_404(Sale, id=sale_id)
        with transaction.atomic():
            sale.book.update_total_sales(-sale.quantity)
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
