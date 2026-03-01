# views/cover_upload.py
import os
import uuid
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'gif', 'png', 'webp', 'jxl'}
UPLOAD_DIR = os.path.join(settings.BASE_DIR, 'static', 'img', 'covers')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class CoverImageUploadView(APIView):
    """
    POST /api/books/upload-cover/
    Accepts a multipart file upload and saves it to static/img/covers/
    Returns the path that can be stored in Book.cover_image_path
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES['file']

        # Validate file type
        if not allowed_file(file.name):
            return Response(
                {'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate file size (e.g., max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if file.size > max_size:
            return Response(
                {'error': 'File too large. Maximum size is 5MB.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate unique filename to avoid collisions
        ext = file.name.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{ext}"

        # Ensure upload directory exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Save file
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # Return the path to store in the database
        # This path should be accessible via your static file serving
        cover_image_path = f"/static/img/covers/{unique_filename}"

        return Response(
            {'cover_image_path': cover_image_path},
            status=status.HTTP_201_CREATED
        )
