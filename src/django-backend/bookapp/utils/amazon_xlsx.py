"""
Amazon XLSX parser and validator.

Parses an Amazon monthly sales XLSX, validates structure + data across all
supported sheets, and returns preview-ready sale records or error/warning lists.

NOTE: This file is a skeleton. Concrete row-parsing logic inside each
_SheetHandler subclass is not yet implemented.
"""

from abc import ABC, abstractmethod
from decimal import Decimal

from .base_parser import ParseResult, SalesImportParser


# ──────────────────────────────────────────────────────────────────────────────
# Sheet-level abstraction (private to this module)
# ──────────────────────────────────────────────────────────────────────────────

class _SheetHandler(ABC):
    """
    Internal abstraction for a single Amazon XLSX sheet type.

    Each supported sheet (Paperback Royalty, Hardcover Royalty, eBook Royalty,
    KENP) has its own column schema, book-lookup key, and field mapping.
    Subclasses encapsulate that per-sheet logic so AmazonXLSXParser.parse_and_validate
    can iterate over handlers without branching on sheet name.

    Not a subclass of SalesImportParser — it is an internal detail of
    AmazonXLSXParser and receives the parent parser instance to call shared
    helpers (_lookup_book_by_isbn, _compute_author_royalty, etc.).
    """

    #: The exact sheet name as it appears in the XLSX file.
    sheet_name: str

    @abstractmethod
    def parse_rows(
        self,
        worksheet,
        filename: str,
        timestamp: str,
        parser: "AmazonXLSXParser",
    ) -> tuple[list[dict], list[str], list[str]]:
        """
        Parse all data rows from a single worksheet.

        Args:
            worksheet: An openpyxl Worksheet object.
            filename:  Original upload filename (for comment generation).
            timestamp: Import timestamp string (for comment generation).
            parser:    The owning AmazonXLSXParser instance; use its protected
                       helpers (_lookup_book_by_asin, _money, etc.).

        Returns:
            (preview_rows, errors, warnings)
            - preview_rows: list of preview row dicts (empty if any errors).
            - errors:       blocking validation errors for this sheet.
            - warnings:     non-blocking notices (e.g. skipped unsupported rows).
        """
        raise NotImplementedError


# ──────────────────────────────────────────────────────────────────────────────
# Concrete sheet handlers (skeletons — row logic not yet implemented)
# ──────────────────────────────────────────────────────────────────────────────

class _PrintRoyaltySheetHandler(_SheetHandler):
    """
    Handles "Paperback Royalty" and "Hardcover Royalty" sheets.

    Books are identified by ISBN (isbn_13 or isbn_10).
    Sale format: "print".
    Required columns: Title, Author, ISBN, Marketplace, Units Sold,
                      Units Refunded, Currency, Royalty (others ignored).
    """

    def __init__(self, sheet_name: str) -> None:
        # Accepts either "Paperback Royalty" or "Hardcover Royalty"
        self.sheet_name = sheet_name

    def parse_rows(self, worksheet, filename, timestamp, parser):
        raise NotImplementedError(
            f"_PrintRoyaltySheetHandler.parse_rows not yet implemented "
            f"(sheet: {self.sheet_name})"
        )


class _EBookRoyaltySheetHandler(_SheetHandler):
    """
    Handles the "eBook Royalty" sheet.

    Books are identified by Amazon ebook ASIN.
    Sale format: "ebook".
    Required columns: Title, Author, ASIN, Marketplace, Units Sold,
                      Units Refunded, Net Units Sold, Currency, Royalty (others ignored).
    """

    sheet_name = "eBook Royalty"

    def parse_rows(self, worksheet, filename, timestamp, parser):
        raise NotImplementedError(
            "EBookRoyaltySheetHandler.parse_rows not yet implemented"
        )


class _KENPSheetHandler(_SheetHandler):
    """
    Handles the "KENP" sheet (Kindle Unlimited and Audible revenue).

    Only rows where "eBook ASIN" is not "N/A" are supported; other rows
    (audiobook rows) generate a warning and are skipped.
    Books are identified by "eBook ASIN".
    Sale format: "kindle unlimited".
    Required columns: Title, Author, eBook ASIN, Marketplace,
                      Kindle Edition Normalized Pages (KENP), Currency, Royalty (others ignored).
    """

    sheet_name = "KENP"

    def parse_rows(self, worksheet, filename, timestamp, parser):
        raise NotImplementedError(
            "_KENPSheetHandler.parse_rows not yet implemented"
        )


class _AudiobookRoyaltySheetHandler(_SheetHandler):
    """
    Handles the "Audiobook Royalty" sheet.

    This sheet is not supported for import. The handler only validates
    that no data rows are present; if rows exist, a warning is issued.
    """

    sheet_name = "Audiobook Royalty"

    def parse_rows(self, worksheet, filename, timestamp, parser):
        raise NotImplementedError(
            "_AudiobookRoyaltySheetHandler.parse_rows not yet implemented"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Top-level parser
# ──────────────────────────────────────────────────────────────────────────────

#: Sheet handlers for all sheets the parser should attempt to process.
#: Ordered: print sheets first, then ebook, then KENP, then audiobook check.
_SHEET_HANDLERS: list[_SheetHandler] = [
    _PrintRoyaltySheetHandler("Paperback Royalty"),
    _PrintRoyaltySheetHandler("Hardcover Royalty"),
    _EBookRoyaltySheetHandler(),
    _KENPSheetHandler(),
    _AudiobookRoyaltySheetHandler(),
]

#: Names of sheets that must be absent (or empty) — audiobook only for now.
_UNSUPPORTED_SHEET_NAMES = {"Audiobook Royalty"}

#: Names of sheets that count as "supported data sheets" (at least one must be present).
_SUPPORTED_DATA_SHEET_NAMES = {
    "Paperback Royalty",
    "Hardcover Royalty",
    "eBook Royalty",
    "KENP",
}


class AmazonXLSXParser(SalesImportParser):
    """
    Parser for Amazon monthly sales XLSX files.

    The XLSX contains multiple named sheets. This parser:
      1. Opens the XLSX with openpyxl.
      2. Verifies at least one supported data sheet is present.
      3. Dispatches each present sheet to its _SheetHandler.
      4. Merges all preview rows, errors, and warnings into a single ParseResult.

    Month/year is extracted from each sheet's special first row (cell A1 = "Sales Period",
    cell B1 = e.g. "June 2025") — the user does NOT provide it.

    Currency conversion: rows with non-USD currency call _convert_to_usd().
    The base-class stub returns the amount unchanged; real conversion logic
    is to be implemented before this parser is production-ready.
    """

    DISTRIBUTOR_NAME = "Amazon"

    def parse_and_validate(self, file, **kwargs) -> ParseResult:
        """
        Parse and validate an Amazon XLSX file.

        Args:
            file: An UploadedFile (from request.FILES).

        Returns:
            ParseResult. errors blocks preview; warnings are non-blocking.
        """
        filename = file.name or "unknown"
        timestamp = self._capture_timestamp()
        metadata = {"filename": filename, "timestamp": timestamp}

        # ---- open XLSX ----
        try:
            import openpyxl
            workbook = openpyxl.load_workbook(file, data_only=True)
        except Exception:
            return ParseResult(
                errors=["File is not a valid XLSX."],
                metadata=metadata,
            )

        present_sheet_names = set(workbook.sheetnames)

        # ---- at least one supported data sheet must be present ----
        supported_present = present_sheet_names & _SUPPORTED_DATA_SHEET_NAMES
        if not supported_present:
            return ParseResult(
                errors=[
                    "No supported sheets found. Expected at least one of: "
                    + ", ".join(sorted(_SUPPORTED_DATA_SHEET_NAMES)) + "."
                ],
                metadata=metadata,
            )

        # ---- dispatch to sheet handlers ----
        all_preview: list[dict] = []
        all_errors: list[str] = []
        all_warnings: list[str] = []

        for handler in _SHEET_HANDLERS:
            if handler.sheet_name not in present_sheet_names:
                continue
            ws = workbook[handler.sheet_name]
            rows, errors, warnings = handler.parse_rows(ws, filename, timestamp, self)
            all_preview.extend(rows)
            all_errors.extend(errors)
            all_warnings.extend(warnings)

        if all_errors:
            return ParseResult(errors=all_errors, warnings=all_warnings, metadata=metadata)

        return ParseResult(preview=all_preview, warnings=all_warnings, metadata=metadata)
