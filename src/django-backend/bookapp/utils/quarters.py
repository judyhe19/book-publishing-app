# utils/quarters.py
# Shared quarter-range helpers used by royalty reports and financial reports.

from rest_framework import status
from rest_framework.response import Response


# Quarter date ranges (month-day boundaries)
QUARTER_RANGES = {
    1: ("01-01", "03-31"),
    2: ("04-01", "06-30"),
    3: ("07-01", "09-30"),
    4: ("10-01", "12-31"),
}


def quarter_date_range(year, quarter):
    """Return (start_date, end_date) strings for a given year/quarter."""
    start_md, end_md = QUARTER_RANGES[quarter]
    return f"{year:04d}-{start_md}", f"{year:04d}-{end_md}"


def enumerate_quarters(start_year, start_quarter, end_year, end_quarter):
    """Yield (year, quarter) tuples from start to end inclusive."""
    y, q = start_year, start_quarter
    while (y, q) <= (end_year, end_quarter):
        yield y, q
        q += 1
        if q > 4:
            q = 1
            y += 1


def validate_quarter_params(request):
    """
    Parse and validate quarter range query params from a DRF request.

    Returns:
        tuple: (start_year, start_quarter, end_year, end_quarter) on success.
        Response: A 400 error Response if validation fails.
    """
    try:
        start_year = int(request.query_params["start_year"])
        start_quarter = int(request.query_params["start_quarter"])
        end_year = int(request.query_params["end_year"])
        end_quarter = int(request.query_params["end_quarter"])
    except (KeyError, ValueError, TypeError):
        return Response(
            {"detail": "start_year, start_quarter, end_year, and end_quarter are required integers."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not (1 <= start_quarter <= 4 and 1 <= end_quarter <= 4):
        return Response(
            {"detail": "Quarters must be between 1 and 4."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if (start_year, start_quarter) > (end_year, end_quarter):
        return Response(
            {"detail": "Start quarter must not be after end quarter."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return (start_year, start_quarter, end_year, end_quarter)
