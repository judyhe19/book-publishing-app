# serializers/book.py
from rest_framework import serializers
from django.db import transaction

from ..models import Book, Author
from .fields import MonthYearField
from .validators import (
    validate_isbn_13,
    validate_isbn_10,
)


class BookMonthYearField(MonthYearField):
    """Publication-date-specific error wording."""
    default_error_messages = {
        **MonthYearField.default_error_messages,
        "invalid": "Please provide publication date in Month, Year format.",
    }


class BookListSerializer(serializers.ModelSerializer):
    publication_date = MonthYearField(read_only=True)

    # Single-author (Evolution 2)
    author_id = serializers.IntegerField(source="author.id", read_only=True)
    author_name = serializers.CharField(source="author.name", read_only=True)

    # total_sales_to_date is not a model field; it comes from queryset annotation.
    total_sales_to_date = serializers.IntegerField(read_only=True)
    total_author_royalty = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    paid_author_royalty = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    unpaid_author_royalty = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    # Convenience display (optional)
    series_display = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "publication_date",
            "isbn_13",
            "isbn_10",
            "total_sales_to_date",
            "total_author_royalty",
            "paid_author_royalty",
            "unpaid_author_royalty",
            "author_id",
            "author_name",
            "distributor_author_royalty_rate",
            "hand_sold_author_royalty_rate",
            "cover_price",
            "print_cost",
            "cover_image_path",
            "series_name",
            "series_position",
            "series_display",
        ]

    def get_series_display(self, obj):
        # Matches: "Lord of the Rings (3)"
        if obj.series_name and obj.series_position:
            return f"{obj.series_name} ({obj.series_position})"
        return None


class BookDetailSerializer(BookListSerializer):
    """
    Identical to BookListSerializer for now. Exists as a separate class so the
    detail view can diverge later without changing the list endpoint.
    """
    pass


class BookCreateSerializer(serializers.ModelSerializer):
    publication_date = BookMonthYearField()

    # Accept author_id from frontend
    author_id = serializers.PrimaryKeyRelatedField(
        source="author",
        queryset=Author.objects.all(),
        write_only=True,
        error_messages={"does_not_exist": "Author does not exist."},
    )

    # Read-only display
    author_name = serializers.CharField(source="author.name", read_only=True)

    class Meta:
        model = Book
        fields = [
            "title",
            "publication_date",
            "isbn_13",
            "isbn_10",
            "author_id",
            "author_name",
            "distributor_author_royalty_rate",
            "hand_sold_author_royalty_rate",
            "cover_price",
            "print_cost",
            "cover_image_path",
            "series_name",
            "series_position",
        ]

    def validate_isbn_13(self, value):
        return validate_isbn_13(value, required=True)

    def validate_isbn_10(self, value):
        return validate_isbn_10(value)

    def validate(self, attrs):
        error = {}

        if not attrs.get("title"):
            error["title"] = "Title is required."

        if not attrs.get("publication_date"):
            error["publication_date"] = "Publication date is required."

        if not attrs.get("isbn_13"):
            error["isbn_13"] = "ISBN-13 is required."

        if not attrs.get("author"):
            error["author_id"] = "Author is required."

        # Required monetary fields
        if attrs.get("cover_price") is None:
            error["cover_price"] = "Cover price is required."
        if attrs.get("print_cost") is None:
            error["print_cost"] = "Print cost is required."

        # Series/position pairing (DB constraint also enforces, but this gives friendly API errors)
        series_name = attrs.get("series_name")
        series_pos = attrs.get("series_position")
        if (series_name and series_pos is None) or (series_pos is not None and not series_name):
            error["series"] = "If a series is specified, both series name and position must be provided."

        if error:
            raise serializers.ValidationError(error)

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        # author comes in via author_id -> source="author"
        book = Book.objects.create(**validated_data)
        return book


class BookUpdateSerializer(serializers.ModelSerializer):
    """
    PATCH behavior:
    - Any provided fields are updated.
    - author_id can be provided to change the author.
    """
    publication_date = BookMonthYearField(required=False)

    author_id = serializers.PrimaryKeyRelatedField(
        source="author",
        queryset=Author.objects.all(),
        write_only=True,
        required=False,
        error_messages={"does_not_exist": "Author does not exist."},
    )

    author_name = serializers.CharField(source="author.name", read_only=True)

    class Meta:
        model = Book
        fields = [
            "title",
            "publication_date",
            "isbn_13",
            "isbn_10",
            "author_id",
            "author_name",
            "distributor_author_royalty_rate",
            "hand_sold_author_royalty_rate",
            "cover_price",
            "print_cost",
            "cover_image_path",
            "series_name",
            "series_position",
        ]

    def validate_isbn_13(self, value):
        return validate_isbn_13(value, required=False)

    def validate_isbn_10(self, value):
        return validate_isbn_10(value)

    def validate(self, attrs):
        # Friendly validation for series/position pairing on PATCH.
        # Need to consider existing instance values if only one field provided.
        instance = getattr(self, "instance", None)

        series_name = attrs.get("series_name", getattr(instance, "series_name", None))
        series_pos = attrs.get("series_position", getattr(instance, "series_position", None))

        if (series_name and series_pos is None) or (series_pos is not None and not series_name):
            raise serializers.ValidationError(
                {"series": "If a series is specified, both series name and position must be provided."}
            )

        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance