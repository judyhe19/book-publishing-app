import datetime
import re

from rest_framework import serializers
from decimal import Decimal
from ..models import Sale, Book, Author, AuthorSale, AuthorBook


class SaleSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source="book.title", read_only=True)
    author_details = serializers.SerializerMethodField()
    date = MonthYearField(read_only=True)

    class Meta:
        model = Sale
        fields = ["id", "book", "book_title", "date", "quantity", "publisher_revenue", "author_details"]

    def get_author_details(self, obj):
        """Get author details for the sale - royalty amounts and paid status."""
        details = []
        for ars in obj.author_sales.select_related("author").all():
            details.append(
                {
                    "id": ars.author.id,
                    "name": ars.author.name,
                    "royalty_amount": ars.royalty_amount,
                    "paid": ars.author_paid,
                }
            )
        return details


class PlaceholderDecimalField(serializers.DecimalField):
    """
    Convert UI placeholders '--' and blank '' into a validation failure
    instead of letting them cause a 500 DB IntegrityError.
    """
    def to_internal_value(self, data):
        if isinstance(data, str) and data.strip() in ("", "--"):
            self.fail("required")
        return super().to_internal_value(data)

_YYYY_MM = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])$")

class MonthYearField(serializers.Field):
    """
    Accepts only YYYY-MM strings.  Stores as a date (first of month) internally
    and outputs YYYY-MM in responses.
    """
    default_error_messages = {
        "required": "Date is required.",
        "null": "Date is required.",
        "invalid": "Please provide sale date in Month, Year format (YYYY-MM).",
    }

    def to_internal_value(self, data):
        if not isinstance(data, str) or data.strip() == "":
            self.fail("required")
        data = data.strip()
        if not _YYYY_MM.match(data):
            self.fail("invalid")
        year, month = data.split("-")
        return datetime.date(int(year), int(month), 1)

    def to_representation(self, value):
        if isinstance(value, datetime.date):
            return value.strftime("%Y-%m")
        return value


class SaleWriteSerializer(serializers.ModelSerializer):
    """
    Handles both create (POST) and update (PATCH) for sales.
    Used by SaleCreateView and SaleEditView.

    On PATCH (partial=True), DRF automatically makes all fields optional.
    Only fields explicitly sent in the payload are validated.
    """
    author_royalties = serializers.DictField(
        child=serializers.DecimalField(max_digits=10, decimal_places=2),
        required=False,
        write_only=True,
    )
    author_paid = serializers.DictField(
        child=serializers.BooleanField(),
        required=False,
        write_only=True,
    )

    quantity = serializers.IntegerField(
        min_value=1,
        error_messages={
            "required": "Quantity is required.",
            "null": "Quantity is required.",
            "invalid": "Quantity must be a valid integer.",
            "min_value": "Quantity must be a positive integer.",
        },
    )

    publisher_revenue = PlaceholderDecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0"),
        error_messages={
            "required": "Publisher revenue is required.",
            "null": "Publisher revenue is required.",
            "min_value": "Publisher revenue cannot be negative.",
        },
    )

    date = MonthYearField()

    book = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(),
        error_messages={
            "required": "Book is required.",
            "null": "Book is required.",
            "does_not_exist": "Book not found.",
        },
    )

    class Meta:
        model = Sale
        fields = ["book", "quantity", "publisher_revenue", "author_royalties", "author_paid", "date"]

    # ------------------------------------------------------------------
    # Field-level validators (called by DRF)
    # ------------------------------------------------------------------

    def validate_author_royalties(self, value):
        """Validate that no author royalty amounts are negative."""
        negative_errors = []
        for author_id, amount in value.items():
            if amount < 0:
                try:
                    author = Author.objects.get(id=author_id)
                    author_name = author.name
                except Author.DoesNotExist:
                    author_name = str(author_id)
                negative_errors.append(f"Royalty amount for author {author_name} cannot be negative.")

        if negative_errors:
            raise serializers.ValidationError("\n".join(negative_errors))
        return value

    # ------------------------------------------------------------------
    # Cross-field validation
    # ------------------------------------------------------------------

    def validate(self, data):
        """Only cross-field checks remain here — individual fields are validated by DRF."""
        sale_date = data.get("date")   # already a first-of-month date
        book = data.get("book")

        # Compare at month/year granularity
        if sale_date and book:
            pub = book.publication_date
            if (sale_date.year, sale_date.month) < (pub.year, pub.month):
                sale_label = sale_date.strftime("%B %Y")
                pub_label = pub.strftime("%B %Y")
                raise serializers.ValidationError({
                    "date": f"Sale date ({sale_label}) cannot be before book publication date ({pub_label})."
                })

        return data

    def create(self, validated_data):
        """Create a Sale instance and associated AuthorSales."""
        author_royalties = validated_data.pop("author_royalties", {})
        author_paid = validated_data.pop("author_paid", {})
        sale = super().create(validated_data)
        sale.create_author_sales(author_royalties, author_paid)
        return sale

    def update(self, instance, validated_data):
        """
        Update a Sale instance WITHOUT recreating associated AuthorSales.
        (Past sales must not change authors/default royalties retroactively.)
        """
        author_royalties = validated_data.pop("author_royalties", {})
        author_paid = validated_data.pop("author_paid", {})

        sale = super().update(instance, validated_data)

        # Apply explicit overrides ONLY to existing AuthorSale rows (no recreation).
        if author_royalties or author_paid:
            for ars in sale.author_sales.all():
                key = str(ars.author_id)
                if key in author_royalties:
                    ars.royalty_amount = author_royalties[key]
                if key in author_paid:
                    ars.author_paid = bool(author_paid[key])
                ars.save()

        return sale
