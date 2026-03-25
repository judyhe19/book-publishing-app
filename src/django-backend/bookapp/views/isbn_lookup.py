from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..utils.isbn_lookup import IsbnLookup, IsbnLookupError


class IsbnLookupView(APIView):
    """
    Look up book metadata from Google Books by ISBN-10 or ISBN-13.

    GET /api/books/isbn-lookup/?isbn=<isbn>

    Returns the volumeInfo from the first matching Google Books result.
    """

    def get(self, request):
        isbn = request.query_params.get("isbn", "").strip()

        if not isbn:
            return Response(
                {"error": "The 'isbn' query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        lookup = IsbnLookup()
        try:
            data = lookup.fetch(isbn)
            return Response(data)
        except IsbnLookupError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
