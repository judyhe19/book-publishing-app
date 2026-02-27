"""
Ingram Spark CSV parser and validator.

Parses an Ingram Spark sales CSV, validates structure + data, and returns
either a list of preview-ready sale records or a list of error strings.
"""

import csv
import io
import re

from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.utils import timezone

from ..models import Book, AuthorBook

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
    timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
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
        csv_line = row_idx + 2  # 1-indexed, +1 for header

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

    # ISBN format
    if not isbn_raw:
        row_errors.append(f"Row {csv_line}: ISBN is missing.")
    elif not re.match(r"^(\d{13}|\d{9}[\dXx])$", isbn_raw):
        row_errors.append(
            f"Row {csv_line}: ISBN '{isbn_raw}' is not a valid ISBN-10 or ISBN-13."
        )

    # Gross Qty
    gross_qty_raw = (row.get("Gross Qty") or "").strip()
    gross_qty = None
    try:
        gross_qty = int(gross_qty_raw)
        if gross_qty < 0:
            row_errors.append(
                f"Row {csv_line}: Gross Qty must be a non-negative integer (got {gross_qty})."
            )
    except (ValueError, TypeError):
        row_errors.append(
            f"Row {csv_line}: Gross Qty '{gross_qty_raw}' is not a valid integer."
        )

    # Returned Qty must be zero
    returned_qty_raw = (row.get("Returned Qty") or "").strip()
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

    # Net Qty
    net_qty_raw = (row.get("Net Qty") or "").strip()
    net_qty = None
    try:
        net_qty = int(net_qty_raw)
        if gross_qty is not None and net_qty != gross_qty:
            row_errors.append(
                f"Row {csv_line}: Net Qty ({net_qty}) does not equal Gross Qty ({gross_qty})."
            )
        if net_qty < 1:
            row_errors.append(
                f"Row {csv_line}: Net Qty must be at least 1 (got {net_qty})."
            )
    except (ValueError, TypeError):
        row_errors.append(
            f"Row {csv_line}: Net Qty '{net_qty_raw}' is not a valid integer."
        )

    # Net Compensation
    net_comp_raw = (row.get("Net Compensation") or "").strip()
    net_comp = None
    try:
        net_comp = Decimal(net_comp_raw)
        if net_comp < 0:
            row_errors.append(
                f"Row {csv_line}: Net Compensation must be non-negative (got {net_comp_raw})."
            )
    except (InvalidOperation, ValueError, TypeError):
        row_errors.append(
            f"Row {csv_line}: Net Compensation '{net_comp_raw}' is not a valid number."
        )

    # ISBN lookup
    book = None
    if isbn_raw and re.match(r"^(\d{13}|\d{9}[\dXx])$", isbn_raw):
        book = Book.objects.filter(isbn_13=isbn_raw).first()
        if not book:
            book = Book.objects.filter(isbn_10=isbn_raw).first()
        if not book:
            row_errors.append(
                f"Row {csv_line}: No book found with ISBN '{isbn_raw}'."
            )

    # Sale date vs publication date (month/year granularity)
    if book:
        pub = book.publication_date
        if (year, month) < (pub.year, pub.month):
            sale_label = datetime(year, month, 1).strftime("%B %Y")
            pub_label = pub.strftime("%B %Y")
            row_errors.append(
                f"Row {csv_line}: Sale date ({sale_label}) is before "
                f"book '{book.title}' publication date ({pub_label})."
            )

    if row_errors:
        return row_errors, None

    return [], {"book": book, "net_qty": net_qty, "net_comp": net_comp}


def _build_preview_row(row_data, csv_row, sale_date_str, filename, timestamp):
    """Build a single preview row dict from validated data."""
    book = row_data["book"]
    net_qty = row_data["net_qty"]
    net_comp = row_data["net_comp"]

    # Compute author royalty (each book has exactly one author)
    author_book = AuthorBook.objects.filter(book=book).select_related("author").first()
    rate = author_book.royalty_rate if author_book else Decimal("0")
    author_royalty = money(rate * net_comp)

    fmt = (csv_row.get("Format") or "").strip()
    market = (csv_row.get("Sales Market") or "").strip()
    comment = (
        f"Ingram: Format='{fmt}' Market='{market}' "
        f"File='{filename}' ({timestamp})"
    )

    return {
        "book": book.id,
        "book_title": book.title,
        "book_label": f"{book.title} ({book.isbn_13})",
        "author_name": author_book.author.name if author_book else "",
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
