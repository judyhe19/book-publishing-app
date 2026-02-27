# serializers/book.py
from rest_framework import serializers
from django.db import IntegrityError, transaction

from ..models import Book, AuthorBook, Author
from .fields import MonthYearField
from .validators import (
    normalize_author_name,
    validate_royalty_rate,
    rewrite_royalty_errors,
    validate_isbn_13,
    validate_isbn_10,
)


class BookMonthYearField(MonthYearField):
    """Publication-date-specific error wording."""
    default_error_messages = {
        **MonthYearField.default_error_messages,
        "invalid": "Please provide publication date in Month, Year format.",
    }


def _get_or_create_author_by_name(name: str) -> Author:
    """
    DB helper (not a pure validator)
    Case-insensitive "get or create" for Author.name (unique=True).
    Handles race conditions via IntegrityError fallback.
    """
    cleaned = normalize_author_name(name)
    if not cleaned:
        raise serializers.ValidationError({"authors": "Author name cannot be blank."})

    existing = Author.objects.filter(name__iexact=cleaned).first()
    if existing:
        return existing

    try:
        return Author.objects.create(name=cleaned)
    except IntegrityError:
        # race: another request created it
        existing = Author.objects.filter(name__iexact=cleaned).first()
        if existing:
            return existing
        raise


class AuthorBookSerializer(serializers.ModelSerializer):
    """
    Represents the relationship between an Author and a Book,
    including royalty_rate.
    """
    author_id = serializers.IntegerField()
    name = serializers.CharField(source="author.name", read_only=True)
    royalty_rate = serializers.DecimalField(max_digits=5, decimal_places=4)

    class Meta:
        model = AuthorBook
        fields = [
            "author_id",
            "name",
            "royalty_rate",
        ]

    def validate_royalty_rate(self, value):
        return validate_royalty_rate(value)

    def to_internal_value(self, data):
        """Preserve custom royalty_rate error messages, keyed off author_id."""
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as exc:
            if isinstance(exc.detail, dict) and "royalty_rate" in exc.detail:
                aid = data.get("author_id")
                try:
                    author_obj = Author.objects.filter(pk=aid).first()
                    author_label = author_obj.name if author_obj else str(aid)
                except Exception:
                    author_label = str(aid) if aid else "unknown"

                exc.detail["royalty_rate"] = rewrite_royalty_errors(
                    exc.detail["royalty_rate"], author_label
                )
            raise exc


class AuthorBookByNameInputSerializer(serializers.Serializer):
    """
    Input-only serializer used by BookCreate and BookUpdate to allow:
      - author_name (create if missing)
      - royalty_rate
    """
    author_name = serializers.CharField()
    royalty_rate = serializers.DecimalField(max_digits=5, decimal_places=4)

    def validate_author_name(self, value):
        cleaned = normalize_author_name(value)
        if not cleaned:
            raise serializers.ValidationError("Author name cannot be blank.")
        return cleaned

    def validate_royalty_rate(self, value):
        return validate_royalty_rate(value)

    def to_internal_value(self, data):
        """Preserve custom royalty_rate error messages, keyed off author_name."""
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as exc:
            if isinstance(exc.detail, dict) and "royalty_rate" in exc.detail:
                author_label = data.get("author_name") or "unknown"
                exc.detail["royalty_rate"] = rewrite_royalty_errors(
                    exc.detail["royalty_rate"], author_label
                )
            raise exc


class BookListSerializer(serializers.ModelSerializer):
    authors = AuthorBookSerializer(source="authorbook_set", many=True, read_only=True)
    publication_date = MonthYearField(read_only=True)

    # total_sales_to_date is not a model field; it comes from queryset annotation.
    total_sales_to_date = serializers.IntegerField(read_only=True)

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "publication_date",
            "isbn_13",
            "isbn_10",
            "total_sales_to_date",
            "authors",
        ]


class BookDetailSerializer(BookListSerializer):
    """
    Identical to BookListSerializer for now. Exists as a separate class so the
    detail view can diverge later (e.g. include extra nested data) without
    changing the list endpoint.
    """
    pass


class BookCreateSerializer(serializers.ModelSerializer):
    # Input authors by NAME (write-only). Response uses BookDetailSerializer.
    authors = AuthorBookByNameInputSerializer(many=True, write_only=True)
    publication_date = BookMonthYearField()

    class Meta:
        model = Book
        fields = [
            "title",
            "publication_date",
            "isbn_13",
            "isbn_10",
            "authors",
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

        authors = attrs.get("authors", [])
        if not authors:
            error["authors"] = "At least one author is required."
        else:
            # no duplicates by normalized name
            seen = set()
            for entry in authors:
                nm = normalize_author_name(entry.get("author_name", "")).lower()
                if nm in seen:
                    error["authors"] = f"Author {entry.get('author_name')} is added more than once."
                    break
                seen.add(nm)

        if error:
            raise serializers.ValidationError(error)

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        authors_data = validated_data.pop("authors", [])

        book = Book.objects.create(**validated_data)

        for entry in authors_data:
            author = _get_or_create_author_by_name(entry["author_name"])
            AuthorBook.objects.create(
                book=book,
                author=author,
                royalty_rate=entry["royalty_rate"],
            )

        return book


class BookUpdateSerializer(serializers.ModelSerializer):
    """
    PATCH behavior:
    - If "authors" is provided, treat it as full replacement of AuthorBook rows,
      and allow new authors via author_name (created in-transaction).
    - If "authors" is omitted, we do not touch authorbook_set.
    """
    authors = AuthorBookByNameInputSerializer(many=True, required=False, write_only=True)
    publication_date = BookMonthYearField(required=False)

    class Meta:
        model = Book
        fields = [
            "title",
            "publication_date",
            "isbn_13",
            "isbn_10",
            "authors",
        ]

    def validate_isbn_13(self, value):
        return validate_isbn_13(value, required=False)

    def validate_isbn_10(self, value):
        return validate_isbn_10(value)

    def validate(self, attrs):
        # Only validate authors block if it's present on PATCH.
        if "authors" in attrs:
            authors = attrs.get("authors") or []
            if not authors:
                raise serializers.ValidationError({"authors": "At least one author is required."})

            seen = set()
            for entry in authors:
                nm = normalize_author_name(entry.get("author_name", "")).lower()
                if nm in seen:
                    raise serializers.ValidationError(
                        {"authors": f"Author {entry.get('author_name')} is added more than once."}
                    )
                seen.add(nm)

        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        authors_data = validated_data.pop("authors", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if authors_data is not None:
            # Full replace
            instance.authorbook_set.all().delete()

            for entry in authors_data:
                author = _get_or_create_author_by_name(entry["author_name"])
                AuthorBook.objects.create(
                    book=instance,
                    author=author,
                    royalty_rate=entry["royalty_rate"],
                )

        return instance