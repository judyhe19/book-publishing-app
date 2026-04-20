from urllib.parse import urlparse

import requests
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


# Only proxy images from this host to prevent open-proxy abuse.
ALLOWED_IMAGE_HOST = "books.google.com"


class IsbnCoverProxyView(APIView):
    """
    Proxy a Google Books cover image through the backend to avoid CORS issues.

    GET /api/books/isbn-lookup/cover/?url=<google-books-image-url>

    Fetches the image server-side and streams the bytes back to the client.
    Only URLs from books.google.com are accepted.
    """

    def get(self, request):
        url = request.query_params.get("url", "").strip()

        if not url:
            return Response(
                {"error": "The 'url' query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not _is_allowed_url(url):
            return Response(
                {"error": f"Only image URLs from {ALLOWED_IMAGE_HOST} are supported."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            upstream = requests.get(url, timeout=10, stream=True)
        except requests.RequestException as exc:
            return Response(
                {"error": f"Failed to fetch cover image: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if not upstream.ok:
            return Response(
                {"error": f"Cover image request returned HTTP {upstream.status_code}."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        content_type = upstream.headers.get("Content-Type", "image/jpeg")
        return HttpResponse(upstream.content, content_type=content_type)


def _is_allowed_url(url: str) -> bool:
    try:
        host = urlparse(url).hostname or ""
        return host == ALLOWED_IMAGE_HOST or host.endswith(f".{ALLOWED_IMAGE_HOST}")
    except ValueError:
        return False
