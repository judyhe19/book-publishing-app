"""
Abstract base class for all sales import file parsers.

Each concrete parser handles a specific file format and distributor.
Parsers validate uploaded files and produce preview rows ready for bulk creation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP

from django.utils import timezone

from ..models import Book
from ..serializers.sales import SaleWriteSerializer


@dataclass
class ParseResult:
    """
    Standardised return type from every parser's parse_and_validate().

    - preview and errors are mutually exclusive: if errors is non-empty, preview is [].
    - warnings may accompany a valid preview (e.g. unsupported records skipped).
    - metadata always contains at least {"filename": str, "timestamp": str}.
    """

    preview: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class SalesImportParser(ABC):
    """
    Abstract base class for sales import parsers.

    Subclasses must:
      1. Set DISTRIBUTOR_NAME as a class attribute (e.g. "Ingram Spark").
      2. Implement parse_and_validate().

    Protected helpers below handle logic shared across all parsers.
    """

    DISTRIBUTOR_NAME: str

    # ──────────────────────────────────────────────────────────────────────
    # Abstract interface
    # ──────────────────────────────────────────────────────────────────────

    @abstractmethod
    def parse_and_validate(self, file, **kwargs) -> ParseResult:
        """
        Validate an uploaded file and produce preview rows.

        Args:
            file: An UploadedFile from request.FILES.
            **kwargs: Parser-specific parameters (e.g. month/year for Ingram).

        Returns:
            A ParseResult. If result.errors is non-empty, result.preview is [].
            result.warnings may be non-empty even when result.preview is valid.
        """
        ...

    # ──────────────────────────────────────────────────────────────────────
    # Protected helpers
    # ──────────────────────────────────────────────────────────────────────

    def _capture_timestamp(self) -> str:
        """Return the current local time formatted as 'YYYY-MM-DD HH:MM:SS'."""
        return timezone.localtime(timezone.now()).strftime("%Y-%m-%d %H:%M:%S")

    def _money(self, value) -> Decimal:
        """Round a numeric value to 2 decimal places (ROUND_HALF_UP)."""
        return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _lookup_book_by_isbn(self, isbn: str) -> Book | None:
        """
        Look up a Book by ISBN-13 or ISBN-10.

        Returns the matching Book or None. Does NOT append errors — callers are
        responsible for building context-specific error messages (e.g. with a
        CSV row number or sheet/row reference).
        """
        book = Book.objects.filter(isbn_13=isbn).first()
        if not book:
            book = Book.objects.filter(isbn_10=isbn).first()
        return book

    def _lookup_book_by_asin(self, asin: str) -> Book | None:
        """
        Look up a Book by its Amazon ebook ASIN.

        Returns the matching Book or None. Does NOT append errors — callers handle
        error messaging.
        """
        return Book.objects.filter(amazon_asin_ebook=asin).first()

    def _compute_author_royalty(self, book: Book, publisher_revenue_usd: Decimal) -> Decimal:
        """
        Compute the author royalty for a distributor sale.

        royalty = distributor_author_royalty_rate × publisher_revenue_usd
        Result is rounded to 2 decimal places.
        """
        return self._money(book.distributor_author_royalty_rate * publisher_revenue_usd)

    def _validate_with_serializer(
        self, payload: dict, line_ref: str
    ) -> tuple[dict | None, list[str]]:
        """
        Run SaleWriteSerializer validation on a partially-built payload.

        Args:
            payload: Dict of raw sale fields (book id, date, quantity, etc.).
            line_ref: A human-readable location string prepended to error messages,
                      e.g. "Row 5" or "Sheet 'eBook Royalty', row 3".

        Returns:
            (validated_data, errors) where validated_data is the serializer's
            validated_data dict on success, or None on failure.
        """
        serializer = SaleWriteSerializer(data=payload)
        if serializer.is_valid():
            return serializer.validated_data, []

        label_map = {
            "publisher_revenue": "Publisher revenue",
            "quantity": "Quantity",
            "book": "Book",
            "date": "Sale date",
        }
        errors = []
        for field_name, field_errors in serializer.errors.items():
            display = label_map.get(field_name, field_name)
            for error in field_errors:
                errors.append(f"{line_ref}: {display} — {error}")
        return None, errors
