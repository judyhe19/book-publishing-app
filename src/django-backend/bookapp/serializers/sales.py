from rest_framework import serializers
from decimal import Decimal
from ..models import Sale, Book
from .fields import MonthYearField
from bookapp.utils.currency_converter import CurrencyConverter, CurrencyConversionError

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
    is_projected = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = [
            "id", "book", "book_title", "date", "quantity",
            "sale_source", "publisher_revenue", "author_royalty",
            "author_paid", "comment", "author_names",
            "distributor", "format", "currency",
            "publisher_revenue_original", "kenp",
            "is_projected",
        ]

    def get_author_names(self, obj):
        author = getattr(obj.book, "author", None)
        if author:
            return [author.name]
        return []

    def get_is_projected(self, obj):
        """Projected = the sale's book has not been released yet."""
        return not getattr(obj.book, "released", True)


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
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "Quantity must be a valid integer.",
            "min_value": "Quantity must be a positive integer.",
        },
    )

    publisher_revenue = PlaceholderDecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0"),
        required=False,
        allow_null=True,
        error_messages={
            "required": "Publisher revenue is required for distributor sales.",
            "null": "Publisher revenue is required for distributor sales.",
            "min_value": "Publisher revenue must be non-negative.",
        },
    )

    author_royalty = PlaceholderDecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0"),
        required=False,
        allow_null=True,
        read_only=True,
        error_messages={
            "min_value": "Author royalty must be non-negative.",
        },
    )

    sale_source = serializers.ChoiceField(
        choices=Sale.SALE_SOURCE_CHOICES,
        error_messages={
            "required": "Sale source is required.",
            "null": "Sale source is required.",
            "invalid_choice": "Sale source must be 'distributor', 'handsold', or 'kickstarter'.",
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
        max_length=256,
        required=False,
        allow_blank=True,
        allow_null=True,
        error_messages={
            "max_length": "Comment cannot exceed 256 characters."
        },
    )

    distributor = serializers.ChoiceField(
        choices=Sale.DISTRIBUTOR_CHOICES,
        required=False,
        allow_blank=True,
        allow_null=True,
        error_messages={
            "invalid_choice": "Distributor must be 'Ingram Spark', 'Amazon', or 'Other'.",
        },
    )

    format = serializers.ChoiceField(
        choices=Sale.FORMAT_CHOICES,
        required=False,
        default="print",
        error_messages={
            "invalid_choice": "Format must be 'Print', 'eBook', or 'Kindle Unlimited'.",
        },
    )

    currency = serializers.CharField(
        max_length=3,
        required=False,
        default="USD",
    )

    publisher_revenue_original = PlaceholderDecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
        min_value=Decimal("0"),
        error_messages={
            "min_value": "Original revenue must be non-negative.",
        },
    )

    kenp = serializers.IntegerField(
        min_value=0,
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "KENP must be a valid integer.",
            "min_value": "KENP must be non-negative.",
        },
    )

    class Meta:
        model = Sale
        fields = [
            "book", "quantity", "sale_source", "publisher_revenue",
            "author_royalty", "author_paid", "date", "comment",
            "distributor", "format", "currency",
            "publisher_revenue_original", "kenp",
        ]

    # ------------------------------------------------------------------
    # Cross-field validation
    # ------------------------------------------------------------------

    def validate(self, data):
        """Only cross-field checks remain here — individual fields are validated by DRF."""
        sale_date = data.get("date")   # already a first-of-month date
        book = data.get("book")

        # In PATCH requests, if book or sales_source is omitted, we fetch it from instance
        # However, to correctly compute we'll just pull necessary fields from instance if data doesn't have it
        instance = getattr(self, 'instance', None)

        current_book = book if book is not None else (instance.book if instance else None)
        current_source = data.get("sale_source", instance.sale_source if instance else None)
        current_format = data.get("format", instance.format if instance else "print")
        current_qty = data.get("quantity", instance.quantity if instance else None)
        current_kenp = data.get("kenp", instance.kenp if instance else None)
        current_distributor = data.get("distributor", instance.distributor if instance else None)
        current_currency = data.get("currency", instance.currency if instance else "USD")

        # ------------------------------------------------------------------
        # Distributor / sale source rules
        # ------------------------------------------------------------------
        if current_source == "distributor":
            if not current_distributor:
                raise serializers.ValidationError({
                    "distributor": "Distributor is required for distributor sales."
                })
        elif current_source in ("handsold", "kickstarter"):
            # Distributor must not be set for handsold or kickstarter
            if current_distributor:
                data["distributor"] = None

        # ------------------------------------------------------------------
        # Format rules by distributor / sale source
        # ------------------------------------------------------------------
        DISTRIBUTOR_FORMAT_MAP = {
            "Ingram Spark": ["print"],
            "Amazon": ["print", "ebook", "kindle unlimited"],
            "Other": ["print", "ebook"],
        }

        if current_source == "handsold":
            if current_format != "print":
                raise serializers.ValidationError({
                    "format": "Handsold sales must use 'print' format."
                })
        elif current_source == "kickstarter":
            if current_format not in ("print", "ebook"):
                raise serializers.ValidationError({
                    "format": "Kickstarter sales must use 'print' or 'ebook' format."
                })
        elif current_source == "distributor" and current_distributor:
            allowed_formats = DISTRIBUTOR_FORMAT_MAP.get(current_distributor, [])
            if current_format not in allowed_formats:
                raise serializers.ValidationError({
                    "format": f"Format '{current_format}' is not valid for distributor type '{current_distributor}'. "
                              f"Allowed formats for this distributor type: {', '.join(allowed_formats)}."
                })

        # ------------------------------------------------------------------
        # Currency locked to USD for handsold and kickstarter
        # ------------------------------------------------------------------
        if current_source in ("handsold", "kickstarter"):
            if current_currency and current_currency != "USD":
                raise serializers.ValidationError({
                    "currency": "Currency must be USD for handsold and Kickstarter sales."
                })
            data["currency"] = "USD"

        # ------------------------------------------------------------------
        # kenp/quantity mutual exclusion based on format
        # ------------------------------------------------------------------
        if current_format == "kindle unlimited":
            if current_kenp is None:
                raise serializers.ValidationError({
                    "kenp": "KENP is required for Kindle Unlimited sales."
                })
            if current_qty is not None:
                raise serializers.ValidationError({
                    "quantity": "Quantity must be null for Kindle Unlimited sales (use kenp instead)."
                })
            data["quantity"] = None
        else:
            if current_qty is None:
                raise serializers.ValidationError({
                    "quantity": "Quantity is required for print and ebook sales."
                })
            if current_kenp is not None:
                raise serializers.ValidationError({
                    "kenp": "KENP should only be set for Kindle Unlimited sales."
                })
            data["kenp"] = None

        # ------------------------------------------------------------------
        # Currency / original revenue
        # ------------------------------------------------------------------
        if data.get("publisher_revenue_original") is not None:
            if not current_currency:
                raise serializers.ValidationError({
                    "currency": "Currency must be set when providing original revenue."
                })

        # ------------------------------------------------------------------
        # Sale date cannot precede book publication date
        # ------------------------------------------------------------------
        if sale_date and current_book:
            pub = current_book.publication_date
            if (sale_date.year, sale_date.month) < (pub.year, pub.month):
                sale_label = sale_date.strftime("%B %Y")
                pub_label = pub.strftime("%B %Y")
                raise serializers.ValidationError({
                    "date": f"Sale date ({sale_label}) cannot be before book publication date ({pub_label})."
                })

        # Calculate publisher_revenue
        if current_source in ("handsold", "kickstarter"):
            # Computed entirely for handsold and kickstarter, ignore whatever client sends
            if current_qty is not None and current_book is not None:
                # revenue = quantity * (cover_price - print_cost)
                revenue = Decimal(str(current_qty)) * (current_book.cover_price - current_book.print_cost)
                data["publisher_revenue"] = revenue
                data["publisher_revenue_original"] = revenue
        elif current_source == "distributor":
            # Map legacy or USD frontend input
            if data.get("publisher_revenue") is not None and data.get("publisher_revenue_original") is None:
                data["publisher_revenue_original"] = data["publisher_revenue"]

            orig_revenue = data.get("publisher_revenue_original")
            if orig_revenue is not None and current_currency:
                converter = CurrencyConverter()
                try:
                    data["publisher_revenue"] = converter.to_usd(orig_revenue, current_currency)
                except CurrencyConversionError as e:
                    raise serializers.ValidationError({"currency": str(e)})

            # Require the user to provide it for distributor sales (or we computed it above)
            if data.get("publisher_revenue") is None and not (instance and getattr(instance, 'publisher_revenue', None) is not None):
                raise serializers.ValidationError({
                    "publisher_revenue": "Publisher revenue is required for distributor sales."
                })
            # On PATCH, if publisher_revenue is omitted, use the existing one for calculating royalties

        current_revenue = data.get("publisher_revenue", instance.publisher_revenue if instance else None)

        if current_revenue is not None and current_source and current_book:
            if current_source in ("handsold", "kickstarter"):
                # Both handsold and kickstarter use the hand_sold_author_royalty_rate
                rate = current_book.hand_sold_author_royalty_rate
            else:
                rate = current_book.distributor_author_royalty_rate

            data["author_royalty"] = current_revenue * rate

        return data