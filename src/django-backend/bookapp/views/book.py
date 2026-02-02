from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404

from ..models import Book   # adjust import path if needed
from ..serializers.book import BookSerializer

class BookListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        fields = request.query_params.get("fields")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 50))

        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)

        # IMPORTANT: Only return publisher's books
        qs = Book.objects.filter(
            publisher_user=request.user
        ).order_by("id")

        # Search functionality
        q = request.query_params.get("q")
        if q:
            from django.db.models import Q
            # Remove dashes for ISBN search
            c_q = q.replace("-", "").strip()
            qs = qs.filter(
                Q(title__icontains=q) | 
                Q(isbn_13__icontains=c_q) | 
                Q(isbn_10__icontains=c_q)
            )

        # Filter by publication date (only return books published ON or BEFORE this date)
        published_before = request.query_params.get("published_before")
        if published_before:
            qs = qs.filter(publication_date__lte=published_before)

        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size

        books = qs[start:end]

        data = BookSerializer(books, many=True).data

        # Optional: fields filtering
        if fields:
            wanted = {f.strip() for f in fields.split(",")}
            data = [
                {k: v for k, v in item.items() if k in wanted}
                for item in data
            ]

        return Response({
            "count": total,
            "results": data
        })


    def post(self, request):
        serializer = BookSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        # Ownership enforced here
        book = serializer.save(publisher_user=request.user)

        return Response(
            BookSerializer(book).data,
            status=status.HTTP_201_CREATED
        )

class BookDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, book_id):
        book = get_object_or_404(
            Book,
            id=book_id,
            publisher_user=request.user
        )

        serializer = BookSerializer(book, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        book = serializer.save()

        return Response(BookSerializer(book).data)


    def delete(self, request, book_id):
        book = get_object_or_404(
            Book,
            id=book_id,
            publisher_user=request.user
        )

        book.delete()
        return Response(status=204)
