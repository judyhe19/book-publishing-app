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


# ---------------------------------------------------------------------------
# Series position shift helpers
# ---------------------------------------------------------------------------

def _shift_positions_up(series_name, from_pos, exclude_id=None):
    """
    Increment series_position by 1 for all books in the series at >= from_pos.
    Iterates from highest to lowest position to avoid unique-constraint violations.
    """
    qs = Book.objects.filter(series_name=series_name, series_position__gte=from_pos)
    if exclude_id is not None:
        qs = qs.exclude(pk=exclude_id)
    for book in qs.order_by("-series_position"):
        book.series_position += 1
        book.save(update_fields=["series_position"])


def _shift_positions_down(series_name, after_pos, exclude_id=None):
    """
    Decrement series_position by 1 for all books in the series at > after_pos.
    Iterates from lowest to highest position to avoid unique-constraint violations.
    """
    qs = Book.objects.filter(series_name=series_name, series_position__gt=after_pos)
    if exclude_id is not None:
        qs = qs.exclude(pk=exclude_id)
    for book in qs.order_by("series_position"):
        book.series_position -= 1
        book.save(update_fields=["series_position"])


# ---------------------------------------------------------------------------
# Read serializers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Write serializers
# ---------------------------------------------------------------------------

class BookCreateSerializer(serializers.ModelSerializer):
    publication_date = BookMonthYearField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # DRF auto-generates a UniqueTogetherValidator for (series_name, series_position)
        # based on the model's UniqueConstraint. That validator runs BEFORE create(), so it
        # would reject any position that is already occupied — even though our create() logic
        # shifts existing books first. Remove it; uniqueness is maintained by the shift logic.
        self.validators = [
            v for v in self.validators
            if not (
                hasattr(v, "fields")
                and "series_name" in v.fields
                and "series_position" in v.fields
            )
        ]

    # Accept author_id from frontend
    author_id = serializers.PrimaryKeyRelatedField(
        source="author",
        queryset=Author.objects.all(),
        write_only=True,
        error_messages={
            "null": "Author field may not be empty.",
            "required": "Author field may not be empty.",
            "does_not_exist": "Author {pk_value} does not exist.",
        },
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

        # Series/position pairing
        series_name = attrs.get("series_name")
        series_pos = attrs.get("series_position")
        if (series_name and series_pos is None) or (series_pos is not None and not series_name):
            error["series"] = "If a series is specified, both series name and position must be provided."
        elif series_name and series_pos is not None:
            count = Book.objects.filter(series_name=series_name).count()
            if series_pos < 1 or series_pos > count + 1:
                error["series_position"] = (
                    f"Position must be between 1 and {count + 1} for this series."
                )

        if error:
            raise serializers.ValidationError(error)

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        series_name = validated_data.get("series_name")
        series_pos = validated_data.get("series_position")
        if series_name and series_pos is not None:
            _shift_positions_up(series_name, series_pos)
        return Book.objects.create(**validated_data)


class BookUpdateSerializer(serializers.ModelSerializer):
    """
    PATCH behavior:
    - Any provided fields are updated.
    - author_id can be provided to change the author.
    - Series position changes automatically shift other books in the series.
    """
    publication_date = BookMonthYearField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Same as BookCreateSerializer: remove the auto-generated UniqueTogetherValidator
        # for (series_name, series_position). Our update() shifts positions atomically,
        # so the check at validation time would incorrectly block valid moves.
        self.validators = [
            v for v in self.validators
            if not (
                hasattr(v, "fields")
                and "series_name" in v.fields
                and "series_position" in v.fields
            )
        ]

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
        instance = getattr(self, "instance", None)

        new_name = attrs.get("series_name", getattr(instance, "series_name", None))
        new_pos = attrs.get("series_position", getattr(instance, "series_position", None))

        if (new_name and new_pos is None) or (new_pos is not None and not new_name):
            raise serializers.ValidationError(
                {"series": "If a series is specified, both series name and position must be provided."}
            )

        if new_name and new_pos is not None:
            old_name = getattr(instance, "series_name", None)

            # Count books in the target series.
            # If moving within the same series the current book is already counted,
            # so after removing it the max valid insert position is target_count.
            # If changing to a different series, max is target_count + 1.
            target_count = Book.objects.filter(series_name=new_name).count()
            max_pos = target_count if old_name == new_name else target_count + 1

            if new_pos < 1 or new_pos > max_pos:
                raise serializers.ValidationError(
                    {"series_position": f"Position must be between 1 and {max_pos} for this series."}
                )

        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        old_name = instance.series_name
        old_pos = instance.series_position

        new_name = validated_data.get("series_name", old_name)
        new_pos = validated_data.get("series_position", old_pos)

        series_changing = (old_name != new_name) or (old_pos != new_pos)

        if series_changing:
            # Step 1: remove book from its current series slot (if any)
            if old_name and old_pos is not None:
                instance.series_name = None
                instance.series_position = None
                instance.save(update_fields=["series_name", "series_position"])
                _shift_positions_down(old_name, old_pos, exclude_id=instance.pk)

            # Step 2: make room in the target series (if any)
            if new_name and new_pos is not None:
                _shift_positions_up(new_name, new_pos, exclude_id=instance.pk)

        # Step 3: apply all validated fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
