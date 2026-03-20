"""
Sheet handler for the Amazon "KENP" sheet (Kindle Unlimited revenue).
"""

from ._base import _SheetHandler, _cell, _is_blank_row


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

    _REQUIRED_COLS = {
        "Title", "Author", "eBook ASIN", "Marketplace",
        "Kindle Edition Normalized Pages (KENP)", "Currency", "Royalty",
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
        warnings = []

        for row_num, row in enumerate(
            worksheet.iter_rows(min_row=3, values_only=True), start=3
        ):
            if _is_blank_row(row):
                continue

            row_ref = f"Sheet 'KENP', row {row_num}"
            asin_raw = _cell(row, col_map, "eBook ASIN")

            # Skip audiobook/Audible rows where ASIN is "N/A" or absent
            if not asin_raw or asin_raw.upper() == "N/A":
                warnings.append(
                    f"{row_ref}: Skipped — eBook ASIN is '{asin_raw or 'empty'}' "
                    f"(audiobook/Audible row not supported)."
                )
                continue

            row_errors = []

            # KENP page count
            kenp_raw = _cell(row, col_map, "Kindle Edition Normalized Pages (KENP)")
            kenp = None
            try:
                kenp = int(kenp_raw) if kenp_raw else None
                if kenp is None:
                    row_errors.append(f"{row_ref}: KENP cannot be empty.")
            except (ValueError, TypeError):
                row_errors.append(
                    f"{row_ref}: KENP '{kenp_raw}' is not a valid integer."
                )

            # ASIN → book lookup
            book = parser._lookup_book_by_asin(asin_raw)
            if not book:
                row_errors.append(
                    f"{row_ref}: No book found with eBook ASIN '{asin_raw}'."
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

            # Serializer validation (quantity absent — KU rows have kenp instead)
            currency = currency_raw.strip().upper()
            payload = {
                "book": book.id,
                "date": sale_date_str,
                "kenp": kenp,
                "sale_source": "distributor",
                "distributor": parser.DISTRIBUTOR_NAME,
                "format": "kindle unlimited",
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
                "quantity": None,
                "kenp": validated_data["kenp"],
                "format": "kindle unlimited",
                "currency": currency,
                "publisher_revenue": str(parser._money(royalty_usd)),
                "publisher_revenue_original": payload.get("publisher_revenue_original"),
                "author_royalty": str(author_royalty),
                "comment": self._make_comment(marketplace, currency, filename, timestamp),
            })
            preview_rows.append(row_dict)

        if errors:
            return [], errors, warnings
        return preview_rows, [], warnings
