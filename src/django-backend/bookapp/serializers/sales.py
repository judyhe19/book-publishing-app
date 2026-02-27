from rest_framework import serializers
from decimal import Decimal
from ..models import Sale, Book
from .fields import MonthYearField


class SaleMonthYearField(MonthYearField):
    """Sale-specific error wording."""
    default_error_messages = {
        **MonthYearField.default_error_messages,
        "invalid": "Please provide sale date in Month, Year format.",
    }


class SaleSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source="book.title", read_only=True)
    date = MonthYearField(read_only=True)
    author_names = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = [
            "id", "book", "book_title", "date", "quantity",
            "sale_source", "publisher_revenue", "author_royalty",
            "author_paid", "comment", "author_names",
        ]

    def get_author_names(self, obj):
        return list(
            obj.book.authors.values_list("name", flat=True)
        )


class PlaceholderDecimalField(serializers.DecimalField):
    """
    Convert UI placeholders '--' and blank '' into a validation failure
    instead of letting them cause a 500 DB IntegrityError.
    """
    def to_internal_value(self, data):
        if isinstance(data, str) and data.strip() in ("", "--"):
            self.fail("required")
        return super().to_internal_value(data)


class SaleWriteSerializer(serializers.ModelSerializer):
    """
    Handles both create (POST) and update (PATCH) for sales.
    Used by SaleCreateView and SaleEditView.

    On PATCH (partial=True), DRF automatically makes all fields optional.
    Only fields explicitly sent in the payload are validated.
    """

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
            "min_value": "Publisher revenue must be non-negative.",
        },
    )

    # TODO: Once Book has cover_price / print_cost, publisher_revenue for
    #       handsold sales should be auto-computed and this field made
    #       read-only for that sale_source.

    author_royalty = PlaceholderDecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0"),
        error_messages={
            "required": "Author royalty is required.",
            "null": "Author royalty is required.",
            "min_value": "Author royalty must be non-negative.",
        },
    )

    # TODO: Once Book has distributor_royalty_rate / hand_sold_royalty_rate,
    #       author_royalty should be auto-computed as
    #       rate × publisher_revenue and this field made read-only.

    sale_source = serializers.ChoiceField(
        choices=Sale.SALE_SOURCE_CHOICES,
        error_messages={
            "required": "Sale source is required.",
            "null": "Sale source is required.",
            "invalid_choice": "Sale source must be 'distributor' or 'handsold'.",
        },
    )

    date = SaleMonthYearField()

    book = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(),
        error_messages={
            "required": "Book is required.",
            "null": "Book is required.",
            "does_not_exist": "Book not found.",
        },
    )

    author_paid = serializers.BooleanField(required=False, default=False)

    comment = serializers.CharField(
        max_length=256, required=False, allow_blank=True, allow_null=True,
    )

    class Meta:
        model = Sale
        fields = [
            "book", "quantity", "sale_source", "publisher_revenue",
            "author_royalty", "author_paid", "date", "comment",
        ]

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
