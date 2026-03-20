"""
Sheet handler for the Amazon "eBook Royalty" sheet.
"""

from ._base import _SheetHandler, _cell, _is_blank_row


class _EBookRoyaltySheetHandler(_SheetHandler):
    """
    Handles the "eBook Royalty" sheet.

    Books are identified by Amazon ebook ASIN.
    Sale format: "ebook".
    Required columns: Title, Author, ASIN, Marketplace, Units Sold,
                      Units Refunded, Net Units Sold, Currency, Royalty (others ignored).
    """

    sheet_name = "eBook Royalty"

    _REQUIRED_COLS = {
        "Title", "Author", "ASIN", "Marketplace",
        "Units Sold", "Units Refunded", "Net Units Sold", "Currency", "Royalty",
    }

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

            row_ref = f"Sheet 'eBook Royalty', row {row_num}"
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

            # Units Sold and Net Units Sold must match
            units_sold_raw = _cell(row, col_map, "Units Sold")
            net_units_raw = _cell(row, col_map, "Net Units Sold")
            units_sold = None
            net_units = None

            try:
                units_sold = int(units_sold_raw) if units_sold_raw else None
                if units_sold is None:
                    row_errors.append(f"{row_ref}: Units Sold cannot be empty.")
            except (ValueError, TypeError):
                row_errors.append(
                    f"{row_ref}: Units Sold '{units_sold_raw}' is not a valid integer."
                )

            try:
                net_units = int(net_units_raw) if net_units_raw else None
                if net_units is None:
                    row_errors.append(f"{row_ref}: Net Units Sold cannot be empty.")
            except (ValueError, TypeError):
                row_errors.append(
                    f"{row_ref}: Net Units Sold '{net_units_raw}' is not a valid integer."
                )

            if units_sold is not None and net_units is not None and units_sold != net_units:
                row_errors.append(
                    f"{row_ref}: Units Sold ({units_sold}) does not equal "
                    f"Net Units Sold ({net_units})."
                )

            # ASIN → book lookup
            asin_raw = _cell(row, col_map, "ASIN")
            book = None
            if not asin_raw:
                row_errors.append(f"{row_ref}: ASIN is missing.")
            else:
                book = parser._lookup_book_by_asin(asin_raw)
                if not book:
                    row_errors.append(
                        f"{row_ref}: No book found with ASIN '{asin_raw}'."
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
                "quantity": net_units,
                "sale_source": "distributor",
                "distributor": parser.DISTRIBUTOR_NAME,
                "format": "ebook",
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
                "format": "ebook",
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
