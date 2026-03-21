"""
Abstract base class and shared helpers for Amazon XLSX sheet handlers.

Module-level helpers (_parse_sales_period, _build_col_map, _cell, _is_blank_row)
are used directly by concrete handler modules.

_SheetHandler provides the abstract parse_rows interface plus protected helpers
(_extract_header, _check_required_cols, _convert_royalty, _make_comment,
_preview_row_base) that are shared across all concrete sheet handlers.
"""

import datetime
from abc import ABC, abstractmethod
from decimal import Decimal, InvalidOperation

from ..currency_converter import CurrencyConversionError


# ──────────────────────────────────────────────────────────────────────────────
# Module-level helpers
# ──────────────────────────────────────────────────────────────────────────────

def _parse_sales_period(cell_value) -> tuple[int, int]:
    """Parse 'June 2025' → (6, 2025). Raises ValueError if format is not recognised."""
    dt = datetime.datetime.strptime(str(cell_value).strip(), "%B %Y")
    return dt.month, dt.year


def _build_col_map(header_row) -> dict[str, int]:
    """Return {column_name: 0-based_index} for a row of cell values, skipping blank cells."""
    return {
        str(v).strip(): i
        for i, v in enumerate(header_row)
        if v is not None and str(v).strip()
    }


def _cell(row: tuple, col_map: dict[str, int], col_name: str) -> str:
    """Return the stripped string value of a cell by column name, or '' if absent/None."""
    idx = col_map.get(col_name)
    if idx is None or idx >= len(row):
        return ""
    val = row[idx]
    return str(val).strip() if val is not None else ""


def _normalize_isbn(raw: str) -> str:
    """
    Normalize an ISBN string extracted from an Excel cell.

    openpyxl returns numeric cells as Python floats, so a 13-digit ISBN stored
    as a number becomes e.g. '9780441172719.0'.  Stripping the trailing '.0'
    restores the correct string.  Note: ISBN-10 values with a leading zero that
    were stored as numbers in Excel will have lost that zero; this is an
    Excel data-entry issue that cannot be recovered here.
    """
    if "." in raw:
        try:
            raw = str(int(float(raw)))
        except (ValueError, OverflowError):
            pass
    return raw


def _is_blank_row(row: tuple) -> bool:
    """True if every cell in the row is None or an empty/whitespace string."""
    return all(v is None or (isinstance(v, str) and not v.strip()) for v in row)


def _parse_int(raw: str) -> int:
    """
    Parse a whole-number integer from a cell string value.

    openpyxl may return integer cells as Python floats, so quantities like 5
    can arrive as the string '5.0'.  This function handles both representations.

    Raises ValueError if the string does not represent a whole number
    (e.g. '5.5' or 'abc').
    """
    f = float(raw)
    if f != int(f):
        raise ValueError(f"not a whole number: {raw!r}")
    return int(f)


# ──────────────────────────────────────────────────────────────────────────────
# Abstract base handler
# ──────────────────────────────────────────────────────────────────────────────

class _SheetHandler(ABC):
    """
    Internal abstraction for a single Amazon XLSX sheet type.

    Each supported sheet (Paperback Royalty, Hardcover Royalty, eBook Royalty,
    KENP) has its own column schema, book-lookup key, and field mapping.
    Subclasses encapsulate that per-sheet logic so AmazonXLSXParser.parse_and_validate
    can iterate over handlers without branching on sheet name.

    Not a subclass of SalesImportParser — it is an internal detail of
    AmazonXLSXParser. The parent parser instance is passed to parse_rows so
    handlers can call shared helpers (_lookup_book_by_isbn, _money, etc.) and
    access parser._converter for currency conversion.
    """

    #: The exact sheet name as it appears in the XLSX file.
    sheet_name: str

    @abstractmethod
    def parse_rows(
        self,
        worksheet,
        filename: str,
        timestamp: str,
        parser,
    ) -> tuple[list[dict], list[str], list[str]]:
        """
        Parse all data rows from a single worksheet.

        Args:
            worksheet: An openpyxl Worksheet object.
            filename:  Original upload filename (for comment generation).
            timestamp: Import timestamp string (for comment generation).
            parser:    The owning AmazonXLSXParser instance. Use its protected
                       helpers (_lookup_book_by_isbn, _lookup_book_by_asin,
                       _compute_author_royalty, _money) and parser._converter
                       for currency conversion.

        Returns:
            (preview_rows, errors, warnings)
            - preview_rows: list of preview row dicts (empty if any errors).
            - errors:       blocking validation errors for this sheet.
            - warnings:     non-blocking notices (e.g. skipped unsupported rows).
        """
        ...

    # ──────────────────────────────────────────────────────────────────────────
    # Protected helpers shared by concrete handlers
    # ──────────────────────────────────────────────────────────────────────────

    def _extract_header(self, worksheet) -> tuple:
        """
        Read the first two rows of the worksheet:
          - Row 1: validate A1 == 'Sales Period' and parse B1 as 'Month YYYY'.
          - Row 2: build a column-name → 0-based-index map.

        Returns ((month, year), col_map, errors). On any error, (month, year)
        and col_map are None and errors is non-empty.
        """
        a1 = worksheet.cell(row=1, column=1).value
        b1 = worksheet.cell(row=1, column=2).value

        if (str(a1).strip() if a1 is not None else "") != "Sales Period":
            return None, None, [
                f"Sheet '{self.sheet_name}': Expected 'Sales Period' in A1, got '{a1}'."
            ]

        try:
            month, year = _parse_sales_period(b1)
        except (ValueError, TypeError):
            return None, None, [
                f"Sheet '{self.sheet_name}': Cannot parse sales period from B1 "
                f"(got '{b1}'). Expected format: 'June 2025'."
            ]

        header_row = tuple(cell.value for cell in worksheet[2])
        col_map = _build_col_map(header_row)
        return (month, year), col_map, []

    def _check_required_cols(self, col_map: dict, required: set) -> list[str]:
        """Return error strings for any required columns absent from col_map."""
        missing = required - col_map.keys()
        if missing:
            return [
                f"Sheet '{self.sheet_name}': Missing required columns: "
                f"{', '.join(sorted(missing))}."
            ]
        return []

    def _convert_royalty(
        self, royalty_raw: str, currency_raw: str, row_ref: str, parser
    ) -> tuple:
        """
        Parse royalty_raw as a Decimal and convert to USD via parser._converter.

        Returns (royalty_original, royalty_usd, errors). On any failure,
        royalty_original and royalty_usd are None and errors is non-empty.
        """
        if not royalty_raw:
            return None, None, [f"{row_ref}: Royalty cannot be empty."]
        if not currency_raw:
            return None, None, [f"{row_ref}: Currency cannot be empty."]

        try:
            royalty_original = Decimal(royalty_raw)
        except InvalidOperation:
            return None, None, [
                f"{row_ref}: Royalty '{royalty_raw}' is not a valid number."
            ]

        try:
            royalty_usd = parser._converter.to_usd(royalty_original, currency_raw)
        except CurrencyConversionError as exc:
            return None, None, [f"{row_ref}: Currency conversion failed — {exc}"]

        return royalty_original, royalty_usd, []

    def _make_comment(self, marketplace: str, filename: str, timestamp: str) -> str:
        """
        Build the comment string stored on every preview row.

        Spec format:
          Amazon: Market='[Marketplace]' File='[Filename]' Sheet:'[Sheet_name]' ([Timestamp])
        """
        mkt = marketplace[:47] + "..." if len(marketplace) > 50 else marketplace
        fname = filename[:153] + "..." if len(filename) > 156 else filename
        return (
            f"Amazon: Market='{mkt}' File='{fname}' Sheet:'{self.sheet_name}' ({timestamp})"
        )

    def _preview_row_base(self, book, sale_date_str: str, parser) -> dict:
        """Return the fields shared by all Amazon preview row dicts."""
        return {
            "book": book.id,
            "book_title": book.title,
            "book_label": f"{book.title} ({book.isbn_13})",
            "author_name": book.author.name,
            "royalty_rate": str(book.distributor_author_royalty_rate),
            "publication_date": book.publication_date.strftime("%Y-%m"),
            "date": sale_date_str,
            "sale_source": "distributor",
            "distributor": parser.DISTRIBUTOR_NAME,
            "author_paid": False,
        }
