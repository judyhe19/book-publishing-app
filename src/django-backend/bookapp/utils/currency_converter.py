"""
Currency conversion utility using the ratesdb.com free API.

Usage:
    from bookapp.utils.currency_converter import CurrencyConverter

    converter = CurrencyConverter()
    usd_amount = converter.to_usd(Decimal("42.50"), "GBP")
"""

from decimal import Decimal, ROUND_HALF_UP

import requests


RATES_API_URL = "https://free.ratesdb.com/v1/rates"


class CurrencyConversionError(Exception):
    """Raised when the ratesdb.com API returns an error or an unexpected response."""


class CurrencyConverter:
    """
    Converts monetary amounts to USD using the ratesdb.com exchange rate API.

    The API is called at conversion time, so the rate reflects the latest
    published rate for the current date.
    """

    def to_usd(self, amount: Decimal, currency: str) -> Decimal:
        """
        Convert an amount in the given currency to USD.

        Args:
            amount:   The monetary value to convert.
            currency: ISO 4217 currency code of the source currency (e.g. "GBP").

        Returns:
            The equivalent amount in USD, rounded to 2 decimal places.

        Raises:
            CurrencyConversionError: If the API returns an error, the currency is
                unsupported, or the network request fails.
        """
        currency = currency.strip().upper()

        if currency == "USD":
            return Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        rate = self._fetch_rate(currency)
        usd_amount = Decimal(str(amount)) * rate
        return usd_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # ──────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────

    def _fetch_rate(self, from_currency: str) -> Decimal:
        """
        Fetch the latest exchange rate from `from_currency` to USD.

        Returns the rate as a Decimal.
        Raises CurrencyConversionError on any failure.
        """
        try:
            response = requests.get(
                RATES_API_URL,
                params={"from": from_currency, "to": "USD"},
                timeout=10,
            )
        except requests.RequestException as exc:
            raise CurrencyConversionError(
                f"Network error while fetching exchange rate for {from_currency}: {exc}"
            ) from exc

        if not response.ok:
            self._raise_api_error(response, from_currency)

        try:
            body = response.json()
        except ValueError as exc:
            raise CurrencyConversionError(
                f"Invalid JSON response from exchange rate API for {from_currency}."
            ) from exc

        if "errors" in body:
            message = body["errors"].get("message", "Unknown API error.")
            raise CurrencyConversionError(
                f"Exchange rate API error for {from_currency}: {message}"
            )

        try:
            rate = body["data"]["rates"]["USD"]
        except (KeyError, TypeError) as exc:
            raise CurrencyConversionError(
                f"Unexpected response structure from exchange rate API for {from_currency}."
            ) from exc

        return Decimal(str(rate))

    def _raise_api_error(self, response, from_currency: str) -> None:
        """Parse an error HTTP response and raise CurrencyConversionError."""
        status = response.status_code
        try:
            body = response.json()
            message = body.get("errors", {}).get("message", response.text)
        except ValueError:
            message = response.text

        if status == 422:
            raise CurrencyConversionError(
                f"Unsupported or invalid currency code '{from_currency}': {message}"
            )
        if status == 429:
            raise CurrencyConversionError(
                "Exchange rate API rate limit reached. Try again later."
            )
        if status == 404:
            raise CurrencyConversionError(
                f"No exchange rate data found for '{from_currency}'."
            )
        raise CurrencyConversionError(
            f"Exchange rate API returned HTTP {status} for '{from_currency}': {message}"
        )
