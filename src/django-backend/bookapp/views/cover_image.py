# views/cover_image.py
import mimetypes
import os

from django.conf import settings
from django.http import Http404, HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

COVERS_DIR = os.path.join(settings.BASE_DIR, "static", "img", "covers")
COVERS_URL_PREFIX = "/static/img/covers/"


class CoverImageView(APIView):
    """
    GET /api/books/cover-image/?path=/static/img/covers/{filename}

    Serves the original full-resolution cover image file.
    Only paths within /static/img/covers/ are allowed.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        path_param = request.query_params.get("path", "")

        if not path_param.startswith(COVERS_URL_PREFIX):
            raise Http404("Invalid path")

        filename = path_param[len(COVERS_URL_PREFIX):]

        # Prevent directory traversal
        if not filename or "/" in filename or "\\" in filename or ".." in filename:
            raise Http404("Invalid filename")

        file_path = os.path.join(COVERS_DIR, filename)

        if not os.path.isfile(file_path):
            raise Http404("Cover not found")

        content_type, _ = mimetypes.guess_type(file_path)
        content_type = content_type or "application/octet-stream"

        with open(file_path, "rb") as f:
            return HttpResponse(f.read(), content_type=content_type)
