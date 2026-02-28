# views/series.py
from django.db import transaction
from django.db.models import Count, F
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Book


class SeriesListView(APIView):
    """
    GET /api/series/
    Returns all series names with book counts, sorted alphabetically.
    [{"name": "The Expanse", "count": 9}, ...]
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        series = (
            Book.objects.filter(series_name__isnull=False)
            .values("series_name")
            .annotate(count=Count("id"))
            .order_by("series_name")
        )
        return Response([{"name": s["series_name"], "count": s["count"]} for s in series])


class SeriesReorderView(APIView):
    """
    POST /api/series/reorder/
    Body: {"series_name": "...", "book_ids": [3, 1, 5, 2]}

    Reorders books in the series according to book_ids order.
    Books omitted from book_ids are removed from the series.
    All provided book_ids must belong to the given series.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        series_name = request.data.get("series_name")
        book_ids = request.data.get("book_ids")

        if not series_name:
            return Response({"error": "series_name is required."}, status=400)
        if not isinstance(book_ids, list):
            return Response({"error": "book_ids must be a list."}, status=400)

        existing_books = Book.objects.filter(series_name=series_name)
        existing_ids = set(existing_books.values_list("id", flat=True))

        # Validate that all provided ids actually belong to this series
        invalid_ids = [bid for bid in book_ids if bid not in existing_ids]
        if invalid_ids:
            return Response(
                {"error": f"Book IDs not in series '{series_name}': {invalid_ids}"},
                status=400,
            )

        # Step 1: offset all positions by 10000 to avoid uniqueness conflicts
        # during reassignment. Use F() for a single bulk UPDATE.
        existing_books.update(series_position=F("series_position") + 10000)

        # Step 2: assign new sequential positions to kept books
        ids_to_keep = set(book_ids)
        for i, book_id in enumerate(book_ids, start=1):
            Book.objects.filter(pk=book_id).update(series_position=i)

        # Step 3: remove books not in book_ids from the series
        Book.objects.filter(
            series_name=series_name, series_position__gt=9999
        ).update(series_name=None, series_position=None)

        return Response({"status": "ok"})
