"""
Ingram Spark CSV parser and validator.

Parses an Ingram Spark sales CSV, validates structure + data, and returns
either a list of preview-ready sale records or a list of error strings.
"""

import csv
import io
import re

from decimal import Decimal, InvalidOperation

from .base_parser import ParseResult, SalesImportParser


class IngramSparkCSVParser(SalesImportParser):
    """Parser for Ingram Spark monthly sales CSV files."""

    DISTRIBUTOR_NAME = "Ingram Spark"

    _EXPECTED_COLUMNS = [
        "ISBN", "Title", "Author", "Format", "Gross Qty",
        "Returned Qty", "Net Qty", "Net Compensation", "Sales Market",
    ]

    def parse_and_validate(self, file, *, month: int, year: int) -> ParseResult:
        """
        Parse and validate an Ingram Spark CSV.

        Args:
            file:  An UploadedFile (from request.FILES).
            month: int, 1–12.
            year:  int, positive.

        Returns:
            ParseResult. preview is non-empty only when errors is empty.
            warnings is always [].
        """
        filename = file.name or "unknown"
        timestamp = self._capture_timestamp()
        metadata = {"filename": filename, "timestamp": timestamp}

        # ---- decode file ----
        try:
            file_content = file.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            return ParseResult(errors=["File is not a valid CSV (encoding error)."], metadata=metadata)

        # ---- parse CSV ----
        try:
            reader = csv.DictReader(io.StringIO(file_content))
        except csv.Error:
            return ParseResult(errors=["File is not a valid CSV."], metadata=metadata)

        # ---- validate columns ----
        if reader.fieldnames is None:
            return ParseResult(errors=["File is not a valid CSV (no header row)."], metadata=metadata)

        actual_columns = [c.strip() for c in reader.fieldnames]
        col_errors = self._validate_columns(actual_columns)
        if col_errors:
            return ParseResult(errors=col_errors, metadata=metadata)

        # ---- validate rows ----
        errors = []
        preview_rows = []
        sale_date_str = f"{year}-{month:02d}"

        for row_idx, row in enumerate(reader):
            csv_line = row_idx + 2  # header is line 1, first data row is line 2

            # Stop at blank row (Ingram format: blank + totals at end)
            isbn_raw = (row.get("ISBN") or "").strip()
            if not isbn_raw and not any(
                (row.get(c) or "").strip()
                for c in ["Title", "Author", "Format", "Gross Qty"]
            ):
                break

            row_errors, row_data = self._validate_row(row, csv_line, isbn_raw, sale_date_str)
            errors.extend(row_errors)

            if not row_errors and row_data:
                preview_rows.append(
                    self._build_preview_row(row_data, row, sale_date_str, filename, timestamp)
                )

        if errors:
            return ParseResult(errors=errors, metadata=metadata)

        return ParseResult(preview=preview_rows, metadata=metadata)

    # ──────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────

    def _validate_columns(self, actual_columns: list[str]) -> list[str]:
        """Return error strings if columns don't match expected, else []."""
        if actual_columns == self._EXPECTED_COLUMNS:
            return []

        missing = [c for c in self._EXPECTED_COLUMNS if c not in actual_columns]
        unexpected = [c for c in actual_columns if c not in self._EXPECTED_COLUMNS]
        parts = []
        if missing:
            parts.append(f"Missing columns: {', '.join(missing)}.")
        if unexpected:
            parts.append(f"Unexpected columns: {', '.join(unexpected)}.")
        if not missing and not unexpected:
            parts.append(
                f"Columns are in the wrong order. "
                f"Expected: {', '.join(self._EXPECTED_COLUMNS)}. "
                f"Got: {', '.join(actual_columns)}."
            )
        return parts

    def _validate_row(
        self, row: dict, csv_line: int, isbn_raw: str, sale_date_str: str
    ) -> tuple[list[str], dict | None]:
        """
        Validate a single CSV data row.

        Returns:
            (errors, row_data) where row_data is a dict with parsed values
            (book, net_qty, net_comp) or None if errors.
        """
        row_errors = []

        # Check for extra unmapped fields in this row
        if None in row:
            extra_data = row[None]
            row_errors.append(
                f"Row {csv_line}: Contains {len(extra_data)} unexpected extra column(s)."
            )
            return row_errors, None

        # Validate non-sale textual fields are present
        for field_name in ["Title", "Author", "Format", "Sales Market"]:
            val = (row.get(field_name) or "").strip()
            if not val:
                row_errors.append(f"Row {csv_line}: {field_name} cannot be empty.")

        # Returned Qty must be zero
        returned_qty_raw = (row.get("Returned Qty") or "").strip()
        if not returned_qty_raw:
            row_errors.append(f"Row {csv_line}: Returned Qty cannot be empty.")
        else:
            try:
                returned_qty = int(returned_qty_raw)
                if returned_qty != 0:
                    row_errors.append(
                        f"Row {csv_line}: Returned Qty must be zero (got {returned_qty})."
                    )
            except (ValueError, TypeError):
                row_errors.append(
                    f"Row {csv_line}: Returned Qty '{returned_qty_raw}' is not a valid integer."
                )

        # Gross Qty and Net Qty: validate types, then check equality
        gross_qty_raw = (row.get("Gross Qty") or "").strip()
        net_qty_raw = (row.get("Net Qty") or "").strip()

        gross_qty = None
        net_qty = None

        if not gross_qty_raw:
            row_errors.append(f"Row {csv_line}: Gross Qty cannot be empty.")
        else:
            try:
                gross_qty = int(gross_qty_raw)
            except (ValueError, TypeError):
                row_errors.append(
                    f"Row {csv_line}: Gross Qty '{gross_qty_raw}' is not a valid integer."
                )

        if net_qty_raw:
            try:
                net_qty = int(net_qty_raw)
            except (ValueError, TypeError):
                pass  # Serializer will report the type error with line number

        if gross_qty is not None and net_qty is not None and net_qty != gross_qty:
            row_errors.append(
                f"Row {csv_line}: Net Qty ({net_qty}) does not equal Gross Qty ({gross_qty})."
            )

        # ISBN lookup
        book = None
        if not isbn_raw:
            row_errors.append(f"Row {csv_line}: ISBN is missing.")
        elif not re.match(r"^(\d{13}|\d{9}[\dXx])$", isbn_raw):
            row_errors.append(
                f"Row {csv_line}: ISBN '{isbn_raw}' is not a valid ISBN-10 or ISBN-13."
            )
        else:
            book = self._lookup_book_by_isbn(isbn_raw)
            if not book:
                row_errors.append(
                    f"Row {csv_line}: No book found with ISBN '{isbn_raw}'."
                )

        net_comp_raw = (row.get("Net Compensation") or "").strip()

        # Run through SaleWriteSerializer for business-logic validation
        validated_data = None
        if not row_errors and book:
            rate = book.distributor_author_royalty_rate
            try:
                net_comp_val = Decimal(net_comp_raw)
                author_royalty_val = str(self._money(rate * net_comp_val))
            except (InvalidOperation, ValueError, TypeError):
                author_royalty_val = ""  # Let the serializer catch the invalid decimal

            payload = {
                "book": book.id,
                "date": sale_date_str,
                "quantity": net_qty_raw,
                "sale_source": "distributor",
                "distributor": self.DISTRIBUTOR_NAME,
                "format": "print",
                "publisher_revenue": net_comp_raw,
                "author_royalty": author_royalty_val,
            }

            validated_data, serial_errors = self._validate_with_serializer(
                payload, f"Row {csv_line}"
            )
            row_errors.extend(serial_errors)

        if row_errors:
            return row_errors, None

        return [], {
            "book": validated_data["book"],
            "net_qty": validated_data["quantity"],
            "net_comp": validated_data["publisher_revenue"],
        }

    def _build_preview_row(
        self,
        row_data: dict,
        csv_row: dict,
        sale_date_str: str,
        filename: str,
        timestamp: str,
    ) -> dict:
        """Build a single preview row dict from validated data."""
        book = row_data["book"]
        net_qty = row_data["net_qty"]
        net_comp = row_data["net_comp"]

        rate = book.distributor_author_royalty_rate
        author_royalty = self._compute_author_royalty(book, net_comp)

        raw_fmt = (csv_row.get("Format") or "").strip()
        fmt = raw_fmt[:47] + "..." if len(raw_fmt) > 50 else raw_fmt

        raw_market = (csv_row.get("Sales Market") or "").strip()
        market = raw_market[:47] + "..." if len(raw_market) > 50 else raw_market

        fname = filename[:153] + "..." if len(filename) > 156 else filename

        comment = (
            f"Ingram: Format='{fmt}' Market='{market}' "
            f"File='{fname}' ({timestamp})"
        )

        return {
            "book": book.id,
            "book_title": book.title,
            "book_label": f"{book.title} ({book.isbn_13})",
            "author_name": book.author.name,
            "royalty_rate": str(rate),
            "publication_date": book.publication_date.strftime("%Y-%m"),
            "date": sale_date_str,
            "quantity": net_qty,
            "sale_source": "distributor",
            "distributor": self.DISTRIBUTOR_NAME,
            "format": "print",
            "currency": "USD",
            "publisher_revenue": str(self._money(net_comp)),
            "author_royalty": str(author_royalty),
            "author_paid": False,
            "comment": comment,
        }
