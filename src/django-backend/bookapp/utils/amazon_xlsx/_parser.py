"""
Top-level AmazonXLSXParser and sheet handler registry.
"""

import openpyxl

from ..base_parser import ParseResult, SalesImportParser
from ..currency_converter import CurrencyConverter
from ._audiobook_handler import _AudiobookRoyaltySheetHandler
from ._base import _SheetHandler
from ._ebook_handler import _EBookRoyaltySheetHandler
from ._kenp_handler import _KENPSheetHandler
from ._print_handler import _PrintRoyaltySheetHandler


#: Handlers for all sheets the parser attempts to process.
#: Ordered: print sheets first, then ebook, then KENP, then audiobook check.
_SHEET_HANDLERS: list[_SheetHandler] = [
    _PrintRoyaltySheetHandler("Paperback Royalty"),
    _PrintRoyaltySheetHandler("Hardcover Royalty"),
    _EBookRoyaltySheetHandler(),
    _KENPSheetHandler(),
    _AudiobookRoyaltySheetHandler(),
]

#: Sheet names that count as "supported data sheets" (at least one must be present).
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

    Currency conversion is handled by self._converter (a CurrencyConverter instance).
    Sheet handlers access it via parser._converter.to_usd(amount, currency).
    """

    DISTRIBUTOR_NAME = "Amazon"

    def __init__(self) -> None:
        self._converter = CurrencyConverter()

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

        try:
            workbook = openpyxl.load_workbook(file, data_only=True)
        except Exception:
            return ParseResult(
                errors=["File is not a valid XLSX."],
                metadata=metadata,
            )

        present_sheet_names = set(workbook.sheetnames)

        if not (present_sheet_names & _SUPPORTED_DATA_SHEET_NAMES):
            return ParseResult(
                errors=[
                    "No supported sheets found. Expected at least one of: "
                    + ", ".join(sorted(_SUPPORTED_DATA_SHEET_NAMES)) + "."
                ],
                metadata=metadata,
            )

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
