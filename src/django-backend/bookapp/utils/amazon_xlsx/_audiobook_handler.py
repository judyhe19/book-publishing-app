"""
Sheet handler for the Amazon "Audiobook Royalty" sheet.
"""

from ._base import _SheetHandler, _is_blank_row


class _AudiobookRoyaltySheetHandler(_SheetHandler):
    """
    Handles the "Audiobook Royalty" sheet.

    This sheet is not supported for import. The handler only validates
    that no data rows are present; if rows exist, a warning is issued.
    """

    sheet_name = "Audiobook Royalty"

    def parse_rows(self, worksheet, filename, timestamp, parser):
        for row in worksheet.iter_rows(min_row=3, values_only=True):
            if not _is_blank_row(row):
                return [], [], [
                    "Sheet 'Audiobook Royalty' contains data rows that will not be imported. "
                    "Audiobook royalties are not currently supported."
                ]
        return [], [], []
