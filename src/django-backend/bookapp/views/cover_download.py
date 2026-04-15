import os
import uuid
from urllib.parse import urlparse

import requests
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


ALLOWED_IMAGE_HOST = "books.google.com"
ALLOWED_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
}
UPLOAD_DIR = os.path.join(settings.BASE_DIR, "static", "img", "covers")
MAX_SIZE = 5 * 1024 * 1024  # 5MB


class CoverImageDownloadView(APIView):
    """
    Download a cover image from a Google Books URL and save it to static storage.

    POST /api/books/download-cover/
    Body: { "url": "<google-books-image-url>" }

    Returns the same cover_image_path format as CoverImageUploadView so the
    book creation payload is identical whether the image came from a manual
    upload or an ISBN lookup.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        url = (request.data.get("url") or "").strip()

        if not url:
            return Response(
                {"error": "The 'url' field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not _is_allowed_url(url):
            return Response(
                {"error": f"Only image URLs from {ALLOWED_IMAGE_HOST} are supported."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            upstream = requests.get(url, timeout=10)
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

        content_type = upstream.headers.get("Content-Type", "").split(";")[0].strip()
        ext = ALLOWED_CONTENT_TYPES.get(content_type)
        if not ext:
            return Response(
                {"error": f"Unsupported image type '{content_type}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(upstream.content) > MAX_SIZE:
            return Response(
                {"error": "Cover image exceeds the 5MB size limit."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        with open(file_path, "wb") as f:
            f.write(upstream.content)

        return Response(
            {"cover_image_path": f"/static/img/covers/{unique_filename}"},
            status=status.HTTP_201_CREATED,
        )


def _is_allowed_url(url: str) -> bool:
    try:
        host = urlparse(url).hostname or ""
        return host == ALLOWED_IMAGE_HOST or host.endswith(f".{ALLOWED_IMAGE_HOST}")
    except ValueError:
        return False
