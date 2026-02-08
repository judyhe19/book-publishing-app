# serializers/book.py
from rest_framework import serializers
import re
from decimal import Decimal
from django.db import IntegrityError

from ..models import Book, AuthorBook, Author


def _normalize_isbn(value):
    """
    Allow users to type ISBNs with hyphens/spaces.
    We store the normalized version (digits, and possibly trailing X for ISBN-10).
    """
    if value in (None, ""):
        return value
    return re.sub(r"[\s\-]", "", str(value)).strip()


def _normalize_author_name(value: str) -> str:
    # normalize spacing (matches AuthorCreateSerializer behavior)
    return " ".join(str(value).split()).strip()


def _is_isbn10_format(v: str) -> bool:
    # 9 digits + final digit or X/x
    return bool(re.fullmatch(r"\d{9}[\dXx]$", v))


def _get_or_create_author_by_name(name: str) -> Author:
    """
    Case-insensitive "get or create" for Author.name (unique=True).
    Handles race conditions via IntegrityError fallback.
    """
    cleaned = _normalize_author_name(name)
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


# ------------------------------------
# AuthorBook (shared, simple serializer)
# ------------------------------------

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
        if value is None:
            raise serializers.ValidationError("Royalty rate is required.")
        if value < Decimal("0"):
            raise serializers.ValidationError("Royalty rate cannot be negative.")
        if value > Decimal("1"):
            raise serializers.ValidationError("Royalty rate must be less than or equal to 1 (decimal percentage).")
        return value

    def to_internal_value(self, data):
        """
        Preserve your custom royalty_rate error messages.
        (Used by BookUpdate when authors are provided as author_id.)
        """
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as exc:
            if isinstance(exc.detail, dict) and "royalty_rate" in exc.detail:
                errors = exc.detail["royalty_rate"]
                if not isinstance(errors, list):
                    errors = [errors]

                aid = data.get("author_id")
                try:
                    author_obj = Author.objects.filter(pk=aid).first()
                    author_name = author_obj.name if author_obj else str(aid)
                except Exception:
                    author_name = str(aid) if aid else "unknown"

                new_errors = []
                for e in errors:
                    code = getattr(e, "code", None)

                    if code == "invalid":
                        new_errors.append(
                            f"Royalty rate for author {author_name} must be a positive valid decimal number."
                        )
                    elif code in ("max_digits", "max_whole_digits"):
                        new_errors.append(
                            f"Royalty rate for author {author_name} must calculate to a valid percentage (e.g. 0.15)."
                        )
                    else:
                        msg = str(e)
                        if "negative" in msg.lower():
                            new_errors.append(
                                f"Royalty rate for author {author_name} cannot be negative."
                            )
                        elif "less than or equal to 1" in msg.lower() or "exceed" in msg.lower():
                            new_errors.append(
                                f"Royalty rate for author {author_name} must be less than or equal to 1 (decimal percentage)."
                            )
                        else:
                            new_errors.append(msg)

                exc.detail["royalty_rate"] = new_errors
            raise exc


# ------------------------------------
# WRITE input serializer (author by name)
# ------------------------------------

class AuthorBookByNameInputSerializer(serializers.Serializer):
    """
    Input-only serializer used by BookCreate and BookUpdate to allow:
      - author_name (create if missing)
      - royalty_rate
    """
    author_name = serializers.CharField()
    royalty_rate = serializers.DecimalField(max_digits=5, decimal_places=4)

    def validate_author_name(self, value):
        cleaned = _normalize_author_name(value)
        if not cleaned:
            raise serializers.ValidationError("Author name cannot be blank.")
        return cleaned

    def validate_royalty_rate(self, value):
        if value is None:
            raise serializers.ValidationError("Royalty rate is required.")
        if value < Decimal("0"):
            raise serializers.ValidationError("Royalty rate cannot be negative.")
        if value > Decimal("1"):
            raise serializers.ValidationError("Royalty rate must be less than or equal to 1 (decimal percentage).")
        return value

    def to_internal_value(self, data):
        """
        Preserve custom royalty_rate error messages, but keyed off author_name
        (since we don't have author_id here).
        """
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as exc:
            if isinstance(exc.detail, dict) and "royalty_rate" in exc.detail:
                errors = exc.detail["royalty_rate"]
                if not isinstance(errors, list):
                    errors = [errors]

                author_name = data.get("author_name") or "unknown"

                new_errors = []
                for e in errors:
                    code = getattr(e, "code", None)
                    if code == "invalid":
                        new_errors.append(
                            f"Royalty rate for author {author_name} must be a positive valid decimal number."
                        )
                    elif code in ("max_digits", "max_whole_digits"):
                        new_errors.append(
                            f"Royalty rate for author {author_name} must calculate to a valid percentage (e.g. 0.15)."
                        )
                    else:
                        msg = str(e)
                        if "negative" in msg.lower():
                            new_errors.append(f"Royalty rate for author {author_name} cannot be negative.")
                        elif "less than or equal to 1" in msg.lower() or "exceed" in msg.lower():
                            new_errors.append(
                                f"Royalty rate for author {author_name} must be less than or equal to 1 (decimal percentage)."
                            )
                        else:
                            new_errors.append(msg)

                exc.detail["royalty_rate"] = new_errors
            raise exc


# ------------------------------------
# READ serializers (GET)
# ------------------------------------

class BookListSerializer(serializers.ModelSerializer):
    authors = AuthorBookSerializer(source="authorbook_set", many=True, read_only=True)

    # ✅ total_sales_to_date is no longer a model field; it comes from queryset annotation.
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
    pass


# ------------------------------------
# WRITE serializers (POST / PATCH)
# ------------------------------------

class BookCreateSerializer(serializers.ModelSerializer):
    # Input authors by NAME (write-only). Response uses BookDetailSerializer.
    authors = AuthorBookByNameInputSerializer(many=True, write_only=True)

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
        v = _normalize_isbn(value)
        if not v:
            raise serializers.ValidationError("ISBN-13 is required.")
        if not v.isdigit():
            raise serializers.ValidationError("ISBN-13 must contain only digits.")
        if len(v) != 13:
            raise serializers.ValidationError("ISBN-13 must be exactly 13 digits.")
        return v

    # CHANGED: allow trailing X (and store as uppercase X)
    def validate_isbn_10(self, value):
        if value in (None, ""):
            return value
        v = _normalize_isbn(value)
        if len(v) != 10:
            raise serializers.ValidationError("ISBN-10 must be exactly 10 characters.")
        if not _is_isbn10_format(v):
            raise serializers.ValidationError("ISBN-10 must be 9 digits followed by a digit or X.")
        return v.upper()

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
                nm = _normalize_author_name(entry.get("author_name", "")).lower()
                if nm in seen:
                    error["authors"] = f"Author {entry.get('author_name')} is added more than once."
                    break
                seen.add(nm)

        if error:
            raise serializers.ValidationError(error)

        return attrs

    def create(self, validated_data):
        authors_data = validated_data.pop("authors", [])

        # Create book first; author creation + AuthorBook rows occur in the same DB transaction
        # (transaction.atomic is enforced in the view).
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
        v = _normalize_isbn(value)
        if not v.isdigit():
            raise serializers.ValidationError("ISBN-13 must contain only digits.")
        if len(v) != 13:
            raise serializers.ValidationError("ISBN-13 must be exactly 13 digits.")
        return v

    # CHANGED: allow trailing X (and store as uppercase X)
    def validate_isbn_10(self, value):
        if value in (None, ""):
            return value
        v = _normalize_isbn(value)
        if len(v) != 10:
            raise serializers.ValidationError("ISBN-10 must be exactly 10 characters.")
        if not _is_isbn10_format(v):
            raise serializers.ValidationError("ISBN-10 must be 9 digits followed by a digit or X.")
        return v.upper()

    def validate(self, attrs):
        # Only validate authors block if it's present on PATCH.
        if "authors" in attrs:
            authors = attrs.get("authors") or []
            if not authors:
                raise serializers.ValidationError({"authors": "At least one author is required."})

            seen = set()
            for entry in authors:
                nm = _normalize_author_name(entry.get("author_name", "")).lower()
                if nm in seen:
                    raise serializers.ValidationError(
                        {"authors": f"Author {entry.get('author_name')} is added more than once."}
                    )
                seen.add(nm)

        return attrs

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
