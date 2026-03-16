"""
Ingram Spark CSV parser and validator.

Parses an Ingram Spark sales CSV, validates structure + data, and returns
either a list of preview-ready sale records or a list of error strings.
"""

import csv
import io
import re

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.utils import timezone

from ..models import Book
from ..serializers.sales import SaleWriteSerializer

EXPECTED_COLUMNS = [
    "ISBN", "Title", "Author", "Format", "Gross Qty",
    "Returned Qty", "Net Qty", "Net Compensation", "Sales Market",
]


def money(x):
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def parse_and_validate(csv_file, month, year):
    """
    Parse and validate an Ingram Spark CSV.

    Args:
        csv_file: An UploadedFile (from request.FILES).
        month: int, 1-12.
        year: int, positive.

    Returns:
        (preview_rows, errors, metadata) where:
        - preview_rows: list of dicts if valid, [] if errors.
        - errors: list of error strings, [] if valid.
        - metadata: dict with "filename" and "timestamp".
    """
    filename = csv_file.name or "unknown"
    timestamp = timezone.localtime(timezone.now()).strftime("%Y-%m-%d %H:%M:%S")
    metadata = {"filename": filename, "timestamp": timestamp}

    # ---- decode file ----
    try:
        file_content = csv_file.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        return [], ["File is not a valid CSV (encoding error)."], metadata

    # ---- parse CSV ----
    try:
        reader = csv.DictReader(io.StringIO(file_content))
    except csv.Error:
        return [], ["File is not a valid CSV."], metadata

    # ---- validate columns ----
    if reader.fieldnames is None:
        return [], ["File is not a valid CSV (no header row)."], metadata

    actual_columns = [c.strip() for c in reader.fieldnames]
    col_errors = _validate_columns(actual_columns)
    if col_errors:
        return [], col_errors, metadata

    # ---- validate rows ----
    errors = []
    preview_rows = []
    sale_date_str = f"{year}-{month:02d}"

    for row_idx, row in enumerate(reader):
        csv_line = row_idx + 2  # file line number (header is line 1, first data row is line 2)

        # Stop at blank row (Ingram format: blank + totals at end)
        isbn_raw = (row.get("ISBN") or "").strip()
        if not isbn_raw and not any(
            (row.get(c) or "").strip()
            for c in ["Title", "Author", "Format", "Gross Qty"]
        ):
            break

        row_errors, row_data = _validate_row(row, csv_line, isbn_raw, month, year)
        errors.extend(row_errors)

        if not row_errors and row_data:
            preview_rows.append(
                _build_preview_row(row_data, row, sale_date_str, filename, timestamp)
            )

    if errors:
        return [], errors, metadata

    return preview_rows, [], metadata

def _validate_columns(actual_columns):
    """Return list of error strings if columns don't match expected, else []."""
    if actual_columns == EXPECTED_COLUMNS:
        return []

    missing = [c for c in EXPECTED_COLUMNS if c not in actual_columns]
    unexpected = [c for c in actual_columns if c not in EXPECTED_COLUMNS]
    parts = []
    if missing:
        parts.append(f"Missing columns: {', '.join(missing)}.")
    if unexpected:
        parts.append(f"Unexpected columns: {', '.join(unexpected)}.")
    if not missing and not unexpected:
        parts.append(
            f"Columns are in the wrong order. "
            f"Expected: {', '.join(EXPECTED_COLUMNS)}. "
            f"Got: {', '.join(actual_columns)}."
        )
    return parts


def _validate_row(row, csv_line, isbn_raw, month, year):
    """
    Validate a single CSV data row.

    Returns:
        (errors, row_data) where row_data is a dict with parsed values
        (book, net_qty, net_comp) or None if errors.
    """
    row_errors = []

    # Check for extra unmapped fields in this specific row
    if None in row:
        extra_data = row[None]
        row_errors.append(f"Row {csv_line}: Contains {len(extra_data)} unexpected extra column(s).")
        return row_errors, None

    # First, validate constraints specific to Ingram CSV math
    # Validate non-sale textual fields are present
    for field in ["Title", "Author", "Format", "Sales Market"]:
        val = (row.get(field) or "").strip()
        if not val:
            row_errors.append(f"Row {csv_line}: {field} cannot be empty.")

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

    # Net Qty type/range is also validated by the serializer below; parse here only for equality check
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
        book = Book.objects.filter(isbn_13=isbn_raw).first()
        if not book:
            book = Book.objects.filter(isbn_10=isbn_raw).first()
        if not book:
            row_errors.append(
                f"Row {csv_line}: No book found with ISBN '{isbn_raw}'."
            )

    net_comp_raw = (row.get("Net Compensation") or "").strip()

    # If basic CSV lookup/math rules passed, run through SaleWriteSerializer
    # All proposed sales records must be legal to import: each row's ISBN must match a book in the system and each row must result in a sales record that meets def 16.
    validated_data = None
    if not row_errors and book:
        # Use distributor royalty rate directly from the book
        rate = book.distributor_author_royalty_rate

        # Try to parse net_comp so we can calculate the royalty
        try:
            net_comp_val = Decimal(net_comp_raw)
            author_royalty_val = str(money(rate * net_comp_val))
        except (InvalidOperation, ValueError, TypeError):
            author_royalty_val = ""  # Let the serializer catch the invalid decimal format

        sale_date_str = f"{year}-{month:02d}"

        payload = {
            "book": book.id,
            "date": sale_date_str,
            "quantity": net_qty_raw,
            "sale_source": "distributor",
            "publisher_revenue": net_comp_raw,
            "author_royalty": author_royalty_val,
        }

        serializer = SaleWriteSerializer(data=payload)
        if not serializer.is_valid():
            # Format DRF validation errors for the CSV row
            for field, field_errors in serializer.errors.items():
                for error in field_errors:
                    label_map = {
                        "publisher_revenue": "Net Compensation",
                        "quantity": "Net Qty",
                        "book": "Book",
                        "date": "Sale date"
                    }
                    display_field = label_map.get(field, field)
                    row_errors.append(f"Row {csv_line}: {display_field} logic error: {error}")
        else:
            validated_data = serializer.validated_data

    if row_errors:
        return row_errors, None

    # Passed all rules + serializer validation! Return the native python objects.
    return [], {
        "book": validated_data["book"],
        "net_qty": validated_data["quantity"],
        "net_comp": validated_data["publisher_revenue"]
    }


def _build_preview_row(row_data, csv_row, sale_date_str, filename, timestamp):
    """Build a single preview row dict from validated data."""
    book = row_data["book"]
    net_qty = row_data["net_qty"]
    net_comp = row_data["net_comp"]

    # Use distributor royalty rate and author directly from the book
    rate = book.distributor_author_royalty_rate
    author_royalty = money(rate * net_comp)

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
        "publisher_revenue": str(money(net_comp)),
        "author_royalty": str(author_royalty),
        "author_paid": False,
        "comment": comment,
    }