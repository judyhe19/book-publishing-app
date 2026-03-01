# views/cover_thumbnail.py
import io
import os

from django.conf import settings
from django.http import Http404, HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from PIL import Image

COVERS_DIR = os.path.join(settings.BASE_DIR, "static", "img", "covers")
THUMBNAIL_SIZE = (80, 120)  # max (width, height), aspect ratio preserved
COVERS_URL_PREFIX = "/static/img/covers/"


class CoverThumbnailView(APIView):
    """
    GET /api/books/cover-thumbnail/?path=/static/img/covers/{filename}

    Returns a JPEG thumbnail (max 80x120) of the requested cover image.
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

        try:
            with Image.open(file_path) as img:
                img.thumbnail(THUMBNAIL_SIZE, Image.LANCZOS)
                if img.mode in ("RGBA", "P", "LA"):
                    img = img.convert("RGB")
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=85, optimize=True)
                buf.seek(0)
                return HttpResponse(buf.read(), content_type="image/jpeg")
        except Exception:
            raise Http404("Could not process image")
