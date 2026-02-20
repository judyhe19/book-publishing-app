"""
Shared custom serializer fields.

INTERNAL NOTE — Date storage convention
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
All dates in this application are meaningful only at **month/year** granularity.
The API accepts and returns dates as ``YYYY-MM`` strings (e.g. ``"2023-01"``).

At the database level, Django's ``DateField`` (SQL ``DATE``) is the only viable
column type — there is no native month/year type in SQL.  We normalise every
date to the **first of the month** (day = 1) before saving.  The day component
is purely an internal storage artefact and is never exposed through the API.

This convention is enforced by ``MonthYearField`` below, which is used by both
the Sale and Book serializers.
"""
import datetime
import re

from rest_framework import serializers

_YYYY_MM = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])$")


class MonthYearField(serializers.Field):
    """
    DRF field that accepts **only** ``YYYY-MM`` strings on input, converts them
    to ``datetime.date(year, month, 1)`` for storage, and serialises back to
    ``YYYY-MM`` on output.  The day is always set to 1 internally.
    """
    default_error_messages = {
        "required": "Date is required.",
        "null": "Date is required.",
        "invalid": "Please provide date in Month, Year format.",
    }

    def to_internal_value(self, data):
        if not isinstance(data, str) or data.strip() == "":
            self.fail("required")
        data = data.strip()
        if not _YYYY_MM.match(data):
            self.fail("invalid")
        year, month = data.split("-")
        return datetime.date(int(year), int(month), 1)

    def to_representation(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            # Already a string (shouldn't happen, but safety)
            return value[:7]
        return value.strftime("%Y-%m")
