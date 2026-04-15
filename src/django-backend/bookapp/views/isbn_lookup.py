from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..models import Author
from ..utils.isbn_lookup import IsbnLookup, IsbnLookupError
from ..utils.isbn_normalizer import normalize_volume_info
from ..utils.author_matcher import match_author


class IsbnLookupView(APIView):
    """
    Look up book metadata from Google Books by ISBN-10 or ISBN-13.

    GET /api/books/isbn-lookup/?isbn=<isbn>

    Returns normalized book creation fields extracted from the Google Books result,
    plus author_match — the best matching Author record found in the database,
    or null if no match meets the confidence threshold.
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
            volume_info = lookup.fetch(isbn)
        except IsbnLookupError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        data = normalize_volume_info(volume_info)

        # Attempt to match the first returned author against database records.
        # Author selection/confirmation is handled on the frontend.
        raw_authors = data.get("authors", [])
        if raw_authors:
            candidates = Author.objects.all()
            data["author_match"] = match_author(raw_authors[0], candidates)
        else:
            data["author_match"] = None

        return Response(data)
