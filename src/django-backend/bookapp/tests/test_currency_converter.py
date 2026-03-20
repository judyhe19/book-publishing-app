"""
Tests for bookapp.utils.currency_converter.CurrencyConverter.

Run with:
    python manage.py test bookapp.test_currency_converter
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from bookapp.utils.currency_converter import CurrencyConverter, CurrencyConversionError


def _mock_response(rate=None, status_code=200, json_body=None, raise_for=None):
    """
    Build a mock requests.Response.

    Args:
        rate:        If provided, builds the standard success JSON body
                     {"data": {"rates": {"USD": rate}}}.
        status_code: HTTP status code to return.
        json_body:   Override the entire JSON body (takes precedence over rate).
        raise_for:   If a requests exception class, calling .json() raises it instead.
    """
    mock = MagicMock()
    mock.status_code = status_code
    mock.ok = status_code < 400

    if raise_for:
        mock.json.side_effect = raise_for
    elif json_body is not None:
        mock.json.return_value = json_body
    elif rate is not None:
        mock.json.return_value = {
            "data": {"date": "2026-03-19", "from": "GBP", "rates": {"USD": rate}}
        }

    mock.text = str(json_body or rate or "")
    return mock


class TestToUsdShortCircuit(SimpleTestCase):
    """USD input bypasses the API entirely."""

    def setUp(self):
        self.converter = CurrencyConverter()

    def test_usd_returns_unchanged(self):
        result = self.converter.to_usd(Decimal("100.00"), "USD")
        self.assertEqual(result, Decimal("100.00"))

    def test_usd_lowercase_accepted(self):
        result = self.converter.to_usd(Decimal("50.00"), "usd")
        self.assertEqual(result, Decimal("50.00"))

    def test_usd_rounds_to_two_decimals(self):
        result = self.converter.to_usd(Decimal("10.999"), "USD")
        self.assertEqual(result, Decimal("11.00"))

    def test_usd_rounds_half_up(self):
        # 10.005 → 10.01 (ROUND_HALF_UP)
        result = self.converter.to_usd(Decimal("10.005"), "USD")
        self.assertEqual(result, Decimal("10.01"))

    @patch("bookapp.utils.currency_converter.requests.get")
    def test_usd_makes_no_api_call(self, mock_get):
        self.converter.to_usd(Decimal("42.00"), "USD")
        mock_get.assert_not_called()


class TestToUsdHappyPath(SimpleTestCase):
    """Successful non-USD conversion."""

    def setUp(self):
        self.converter = CurrencyConverter()

    @patch("bookapp.utils.currency_converter.requests.get")
    def test_converts_gbp_to_usd(self, mock_get):
        mock_get.return_value = _mock_response(rate=1.27)
        result = self.converter.to_usd(Decimal("100.00"), "GBP")
        self.assertEqual(result, Decimal("127.00"))

    @patch("bookapp.utils.currency_converter.requests.get")
    def test_result_rounded_to_two_decimals(self, mock_get):
        # 10.00 GBP × 1.2751 = 12.751 → rounds to 12.75
        mock_get.return_value = _mock_response(rate=1.2751)
        result = self.converter.to_usd(Decimal("10.00"), "GBP")
        self.assertEqual(result, Decimal("12.75"))

    @patch("bookapp.utils.currency_converter.requests.get")
    def test_result_rounds_half_up(self, mock_get):
        # 1.00 × 1.005 = 1.005 → 1.01
        mock_get.return_value = _mock_response(rate=1.005)
        result = self.converter.to_usd(Decimal("1.00"), "EUR")
        self.assertEqual(result, Decimal("1.01"))

    @patch("bookapp.utils.currency_converter.requests.get")
    def test_currency_code_case_insensitive(self, mock_get):
        mock_get.return_value = _mock_response(rate=1.27)
        result = self.converter.to_usd(Decimal("50.00"), "gbp")
        self.assertEqual(result, Decimal("63.50"))
        # Verify the API was called with the uppercased code
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["from"], "GBP")

    @patch("bookapp.utils.currency_converter.requests.get")
    def test_api_called_with_correct_params(self, mock_get):
        mock_get.return_value = _mock_response(rate=1.10)
        self.converter.to_usd(Decimal("10.00"), "EUR")
        mock_get.assert_called_once_with(
            "https://free.ratesdb.com/v1/rates",
            params={"from": "EUR", "to": "USD"},
            timeout=10,
        )


class TestToUsdPrecision(SimpleTestCase):
    """Calculations stay in Decimal arithmetic throughout — no float rounding errors."""

    def setUp(self):
        self.converter = CurrencyConverter()

    @patch("bookapp.utils.currency_converter.requests.get")
    def test_float_amount_converted_losslessly(self, mock_get):
        # If a float slips in, str() conversion avoids binary float errors.
        mock_get.return_value = _mock_response(rate=1.0)
        # 42.1 as a float is 42.09999999....; str() → "42.1" → Decimal("42.1")
        result = self.converter.to_usd(42.1, "GBP")
        self.assertEqual(result, Decimal("42.10"))

    @patch("bookapp.utils.currency_converter.requests.get")
    def test_large_rate_precision(self, mock_get):
        # Korean Won: large rate, result should still round correctly
        mock_get.return_value = _mock_response(rate=0.000726)
        result = self.converter.to_usd(Decimal("10000"), "KRW")
        self.assertEqual(result, Decimal("7.26"))

    @patch("bookapp.utils.currency_converter.requests.get")
    def test_string_amount_accepted(self, mock_get):
        mock_get.return_value = _mock_response(rate=1.27)
        result = self.converter.to_usd("100.00", "GBP")
        self.assertEqual(result, Decimal("127.00"))


class TestToUsdApiErrors(SimpleTestCase):
    """API error responses raise CurrencyConversionError."""

    def setUp(self):
        self.converter = CurrencyConverter()

    @patch("bookapp.utils.currency_converter.requests.get")
    def test_unsupported_currency_raises(self, mock_get):
        mock_get.return_value = _mock_response(
            status_code=422,
            json_body={"errors": {"message": "The 'from' currency is unsupported.", "status": 422}},
        )
        with self.assertRaises(CurrencyConversionError) as ctx:
            self.converter.to_usd(Decimal("10.00"), "XYZ")
        self.assertIn("XYZ", str(ctx.exception))
        self.assertIn("unsupported", str(ctx.exception).lower())

    @patch("bookapp.utils.currency_converter.requests.get")
    def test_rate_limit_raises(self, mock_get):
        mock_get.return_value = _mock_response(
            status_code=429,
            json_body={"errors": {"message": "Too many requests.", "status": 429}},
        )
        with self.assertRaises(CurrencyConversionError) as ctx:
            self.converter.to_usd(Decimal("10.00"), "GBP")
        self.assertIn("rate limit", str(ctx.exception).lower())

    @patch("bookapp.utils.currency_converter.requests.get")
    def test_not_found_raises(self, mock_get):
        mock_get.return_value = _mock_response(
            status_code=404,
            json_body={"errors": {"message": "Not found.", "status": 404}},
        )
        with self.assertRaises(CurrencyConversionError) as ctx:
            self.converter.to_usd(Decimal("10.00"), "GBP")
        self.assertIn("GBP", str(ctx.exception))

    @patch("bookapp.utils.currency_converter.requests.get")
    def test_generic_http_error_raises(self, mock_get):
        mock_get.return_value = _mock_response(
            status_code=500,
            json_body={"errors": {"message": "Internal server error.", "status": 500}},
        )
        with self.assertRaises(CurrencyConversionError) as ctx:
            self.converter.to_usd(Decimal("10.00"), "GBP")
        self.assertIn("500", str(ctx.exception))

    @patch("bookapp.utils.currency_converter.requests.get")
    def test_errors_key_in_200_response_raises(self, mock_get):
        # Some APIs return HTTP 200 with an errors body
        mock_get.return_value = _mock_response(
            status_code=200,
            json_body={"errors": {"message": "Something went wrong.", "status": 422}},
        )
        with self.assertRaises(CurrencyConversionError) as ctx:
            self.converter.to_usd(Decimal("10.00"), "GBP")
        self.assertIn("Something went wrong.", str(ctx.exception))


class TestToUsdNetworkAndParseErrors(SimpleTestCase):
    """Network failures and malformed responses raise CurrencyConversionError."""

    def setUp(self):
        self.converter = CurrencyConverter()

    @patch("bookapp.utils.currency_converter.requests.get")
    def test_network_error_raises(self, mock_get):
        import requests as req
        mock_get.side_effect = req.ConnectionError("Connection refused")
        with self.assertRaises(CurrencyConversionError) as ctx:
            self.converter.to_usd(Decimal("10.00"), "GBP")
        self.assertIn("Network error", str(ctx.exception))

    @patch("bookapp.utils.currency_converter.requests.get")
    def test_timeout_raises(self, mock_get):
        import requests as req
        mock_get.side_effect = req.Timeout("Request timed out")
        with self.assertRaises(CurrencyConversionError) as ctx:
            self.converter.to_usd(Decimal("10.00"), "GBP")
        self.assertIn("Network error", str(ctx.exception))

    @patch("bookapp.utils.currency_converter.requests.get")
    def test_invalid_json_raises(self, mock_get):
        mock = MagicMock()
        mock.ok = True
        mock.status_code = 200
        mock.json.side_effect = ValueError("No JSON")
        mock_get.return_value = mock
        with self.assertRaises(CurrencyConversionError) as ctx:
            self.converter.to_usd(Decimal("10.00"), "GBP")
        self.assertIn("Invalid JSON", str(ctx.exception))

    @patch("bookapp.utils.currency_converter.requests.get")
    def test_missing_data_key_raises(self, mock_get):
        mock_get.return_value = _mock_response(status_code=200, json_body={"unexpected": True})
        with self.assertRaises(CurrencyConversionError) as ctx:
            self.converter.to_usd(Decimal("10.00"), "GBP")
        self.assertIn("Unexpected response structure", str(ctx.exception))

    @patch("bookapp.utils.currency_converter.requests.get")
    def test_missing_usd_in_rates_raises(self, mock_get):
        mock_get.return_value = _mock_response(
            status_code=200,
            json_body={"data": {"rates": {"EUR": 0.91}}},  # USD missing
        )
        with self.assertRaises(CurrencyConversionError) as ctx:
            self.converter.to_usd(Decimal("10.00"), "GBP")
        self.assertIn("Unexpected response structure", str(ctx.exception))
