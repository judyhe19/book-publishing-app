"""
Sheet handler for Amazon "Paperback Royalty" and "Hardcover Royalty" sheets.
"""

from ._base import _SheetHandler, _cell, _is_blank_row


class _PrintRoyaltySheetHandler(_SheetHandler):
    """
    Handles "Paperback Royalty" and "Hardcover Royalty" sheets.

    Books are identified by ISBN (isbn_13 or isbn_10).
    Sale format: "print".
    Required columns: Title, Author, ISBN, Marketplace, Units Sold,
                      Units Refunded, Currency, Royalty (others ignored).
    """

    _REQUIRED_COLS = {
        "Title", "Author", "ISBN", "Marketplace",
        "Units Sold", "Units Refunded", "Currency", "Royalty",
    }

    def __init__(self, sheet_name: str) -> None:
        # Accepts either "Paperback Royalty" or "Hardcover Royalty"
        self.sheet_name = sheet_name

    def parse_rows(self, worksheet, filename, timestamp, parser):
        month_year, col_map, errors = self._extract_header(worksheet)
        if errors:
            return [], errors, []

        col_errors = self._check_required_cols(col_map, self._REQUIRED_COLS)
        if col_errors:
            return [], col_errors, []

        month, year = month_year
        sale_date_str = f"{year}-{month:02d}"
        preview_rows = []

        for row_num, row in enumerate(
            worksheet.iter_rows(min_row=3, values_only=True), start=3
        ):
            if _is_blank_row(row):
                continue

            row_ref = f"Sheet '{self.sheet_name}', row {row_num}"
            row_errors = []

            # Units Refunded must be zero
            refunded_raw = _cell(row, col_map, "Units Refunded")
            try:
                refunded = int(refunded_raw) if refunded_raw else None
                if refunded is None:
                    row_errors.append(f"{row_ref}: Units Refunded cannot be empty.")
                elif refunded != 0:
                    row_errors.append(
                        f"{row_ref}: Units Refunded must be zero (got {refunded}); "
                        f"rows with refunds cannot be imported."
                    )
            except (ValueError, TypeError):
                row_errors.append(
                    f"{row_ref}: Units Refunded '{refunded_raw}' is not a valid integer."
                )

            # Units Sold
            units_sold_raw = _cell(row, col_map, "Units Sold")
            units_sold = None
            try:
                units_sold = int(units_sold_raw) if units_sold_raw else None
                if units_sold is None:
                    row_errors.append(f"{row_ref}: Units Sold cannot be empty.")
            except (ValueError, TypeError):
                row_errors.append(
                    f"{row_ref}: Units Sold '{units_sold_raw}' is not a valid integer."
                )

            # ISBN → book lookup
            isbn_raw = _cell(row, col_map, "ISBN")
            book = None
            if not isbn_raw:
                row_errors.append(f"{row_ref}: ISBN is missing.")
            else:
                book = parser._lookup_book_by_isbn(isbn_raw)
                if not book:
                    row_errors.append(
                        f"{row_ref}: No book found with ISBN '{isbn_raw}'."
                    )

            # Royalty + currency conversion
            currency_raw = _cell(row, col_map, "Currency")
            royalty_raw = _cell(row, col_map, "Royalty")
            royalty_original, royalty_usd, conv_errors = self._convert_royalty(
                royalty_raw, currency_raw, row_ref, parser
            )
            row_errors.extend(conv_errors)

            if row_errors:
                errors.extend(row_errors)
                continue

            # Serializer validation
            currency = currency_raw.strip().upper()
            payload = {
                "book": book.id,
                "date": sale_date_str,
                "quantity": units_sold,
                "sale_source": "distributor",
                "distributor": parser.DISTRIBUTOR_NAME,
                "format": "print",
                "currency": currency,
                "publisher_revenue": str(royalty_usd),
            }
            if currency != "USD":
                payload["publisher_revenue_original"] = str(parser._money(royalty_original))

            validated_data, serial_errors = parser._validate_with_serializer(payload, row_ref)
            if serial_errors:
                errors.extend(serial_errors)
                continue

            # Build preview row
            marketplace = _cell(row, col_map, "Marketplace")
            author_royalty = parser._compute_author_royalty(book, royalty_usd)
            row_dict = self._preview_row_base(book, sale_date_str, parser)
            row_dict.update({
                "quantity": validated_data["quantity"],
                "kenp": None,
                "format": "print",
                "currency": currency,
                "publisher_revenue": str(parser._money(royalty_usd)),
                "publisher_revenue_original": payload.get("publisher_revenue_original"),
                "author_royalty": str(author_royalty),
                "comment": self._make_comment(marketplace, currency, filename, timestamp),
            })
            preview_rows.append(row_dict)

        if errors:
            return [], errors, []
        return preview_rows, [], []
