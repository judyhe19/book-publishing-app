# views/branding.py
from urllib.parse import quote

from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class BrandingView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        logo_path = settings.PUBLISHER_LOGO_PATH
        favicon_path = settings.PUBLISHER_FAVICON_PATH

        return Response(
            {
                "publisher_name": settings.PUBLISHER_NAME,
                "app_title": settings.APP_TITLE,
                "publisher_logo_url": f"/api/branding/image/?path={quote(logo_path)}",
                "publisher_favicon_url": f"/api/branding/image/?path={quote(favicon_path)}",
            }
        )