from rest_framework import serializers
from ..models import Book
class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "publication_date",
            "isbn_13",
            "isbn_10",
            "author_royalty_rate",
            "total_sales_to_date",
            "publisher_user",
            "authors",
        ]

        read_only_fields = [
            "id",
            "publisher_user",
            "total_sales_to_date",
        ]