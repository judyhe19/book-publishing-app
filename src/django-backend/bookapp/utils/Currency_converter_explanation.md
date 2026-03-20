# CurrencyConverter

Converts a monetary amount in any supported currency to USD using the [ratesdb.com](https://free.ratesdb.com) free API. The rate fetched always reflects the latest published rate for the current date.

---

## Basic Usage

```python
from decimal import Decimal
from bookapp.utils.currency_converter import CurrencyConverter, CurrencyConversionError

converter = CurrencyConverter()
usd_amount = converter.to_usd(Decimal("42.50"), "GBP")
# Returns Decimal("53.94")  (example — rate varies)
```

### Method signature

```python
converter.to_usd(amount, currency) -> Decimal
```

| Parameter | Type | Description |
|---|---|---|
| `amount` | `Decimal`, `str`, or `float` | The monetary value to convert. |
| `currency` | `str` | ISO 4217 currency code of the source currency (e.g. `"GBP"`, `"EUR"`). Case-insensitive. |

**Returns:** The equivalent amount in USD, always rounded to 2 decimal places (ROUND_HALF_UP).

**USD input is a no-op:** passing `"USD"` skips the API call entirely and just rounds the amount.

---

## Error Handling

All failures raise `CurrencyConversionError`. Always catch it when calling from import logic:

```python
from bookapp.utils.currency_converter import CurrencyConverter, CurrencyConversionError

converter = CurrencyConverter()

try:
    usd = converter.to_usd(royalty, currency)
except CurrencyConversionError as e:
    # Add to your error list and skip the row
    errors.append(f"Row {n}: Could not convert {currency} to USD — {e}")
```

| Situation | Error message contains |
|---|---|
| Unsupported currency code | `"Unsupported or invalid currency code 'XYZ'"` |
| API rate limit hit (429) | `"rate limit"` |
| No data found for currency (404) | `"No exchange rate data found"` |
| Network failure / timeout | `"Network error"` |
| Malformed API response | `"Invalid JSON"` or `"Unexpected response structure"` |

---

## Supported Currencies

| Currency | Code | Currency | Code |
|---|---|---|---|
| Australian dollar | AUD | Norwegian krone | NOK |
| Brazilian real | BRL | Philippine peso | PHP |
| Bulgarian lev | BGN | Polish zloty | PLN |
| Canadian dollar | CAD | Pound sterling | GBP |
| Chinese yuan renminbi | CNY | Romanian leu | RON |
| Croatian kuna | HRK | Russian rouble | RUB |
| Czech koruna | CZK | Singapore dollar | SGD |
| Danish krone | DKK | South African rand | ZAR |
| Euro | EUR | South Korean won | KRW |
| Hong Kong dollar | HKD | Swedish krona | SEK |
| Hungarian forint | HUF | Swiss franc | CHF |
| Icelandic krona | ISK | Thai baht | THB |
| Indian rupee | INR | Turkish lira | TRY |
| Indonesian rupiah | IDR | US dollar | USD |
| Israeli shekel | ILS | Malaysian ringgit | MYR |
| Japanese yen | JPY | Mexican peso | MXN |
| New Zealand dollar | NZD | | |

---

## Notes

- **One API call per conversion.** If you are converting many rows with the same currency (e.g. an entire Amazon XLSX sheet denominated in GBP), you will make one API call per row. A future improvement is to add per-request caching on the `CurrencyConverter` instance to avoid redundant calls and reduce the risk of hitting the 429 rate limit mid-import.
- **Precision:** All arithmetic uses `Decimal` throughout to avoid binary float rounding errors. Passing a `float` or `str` as `amount` is safe — it is converted via `str()` before any arithmetic.
