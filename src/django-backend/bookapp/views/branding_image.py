# views/branding_image.py
import mimetypes
import os

from django.conf import settings
from django.http import Http404, HttpResponse
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

BRANDING_DIR = os.path.join(settings.BASE_DIR, "static", "img", "branding")
BRANDING_URL_PREFIX = "/static/img/branding/"


class BrandingImageView(APIView):
    """
    GET /api/branding/image/?path=/static/img/branding/{filename}

    Serves a branding image file.
    Only paths within /static/img/branding/ are allowed.
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        path_param = request.query_params.get("path", "")

        if not path_param.startswith(BRANDING_URL_PREFIX):
            raise Http404("Invalid path")

        filename = path_param[len(BRANDING_URL_PREFIX):]

        # Prevent directory traversal
        if not filename or "/" in filename or "\\" in filename or ".." in filename:
            raise Http404("Invalid filename")

        file_path = os.path.join(BRANDING_DIR, filename)

        if not os.path.isfile(file_path):
            raise Http404("Branding image not found")

        content_type, _ = mimetypes.guess_type(file_path)
        content_type = content_type or "application/octet-stream"

        with open(file_path, "rb") as f:
            return HttpResponse(f.read(), content_type=content_type)