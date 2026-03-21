# `amazon_xlsx` Package

Parser for Amazon monthly sales XLSX files. Validates structure and data
across all supported sheets and returns preview-ready sale records (or
error/warning lists) without writing anything to the database.

---

## Public interface

```python
from bookapp.utils.amazon_xlsx import AmazonXLSXParser

parser = AmazonXLSXParser()
result = parser.parse_and_validate(request.FILES["file"])

if result.errors:
    # return 400 with result.errors / result.warnings
else:
    # return 200 with result.preview / result.warnings / result.metadata
```

`AmazonXLSXParser` is the **only public symbol** exported by this package.
Everything else is an internal implementation detail (prefixed with `_`).

---

## File overview

### `__init__.py`
Re-exports `AmazonXLSXParser` so callers import from the package, not from
an internal module. Nothing else is exported here.

---

### `_base.py`
Contains two things:

**Module-level helper functions** used directly by all handler modules:

| Function | Purpose |
|---|---|
| `_parse_sales_period(cell_value)` | Parses `"June 2025"` → `(6, 2025)`. Raises `ValueError` on bad format. |
| `_build_col_map(header_row)` | Turns a row of cell values into `{column_name: 0-based index}`. Skips blank cells. |
| `_cell(row, col_map, col_name)` | Safely extracts and strips a cell value by column name. Returns `""` if absent. |
| `_is_blank_row(row)` | Returns `True` if every cell is `None` or whitespace — used to skip footer/empty rows. |

**`_SheetHandler` abstract base class** — the interface every sheet handler must implement, plus protected helpers shared across all handlers:

| Method | Purpose |
|---|---|
| `parse_rows(worksheet, filename, timestamp, parser)` | **Abstract.** Each subclass implements this to parse its sheet's data rows. Returns `(preview_rows, errors, warnings)`. |
| `_extract_header(worksheet)` | Reads row 1 (`"Sales Period"` / `"June 2025"`) and row 2 (column headers). Returns `((month, year), col_map, errors)`. |
| `_check_required_cols(col_map, required)` | Checks that all required column names are present in the header map. Returns error strings for any missing. |
| `_convert_royalty(royalty_raw, currency_raw, row_ref, parser)` | Parses the royalty string as a `Decimal` and converts it to USD via `parser._converter`. Catches `CurrencyConversionError`. Returns `(royalty_original, royalty_usd, errors)`. |
| `_make_comment(marketplace, filename, timestamp)` | Builds the `comment` string stored on the preview row. Format: `Amazon: Market='...' File='...' Sheet:'...' (...)`. |
| `_preview_row_base(book, sale_date_str, parser)` | Returns the dict fields shared by every preview row: `book`, `book_title`, `book_label`, `author_name`, `royalty_rate`, `publication_date`, `date`, `sale_source`, `distributor`, `author_paid`. |

---

### `_print_handler.py` — `_PrintRoyaltySheetHandler`

Handles the **"Paperback Royalty"** and **"Hardcover Royalty"** sheets.
Both use the same column schema and logic, so the same class is instantiated
twice in the handler registry with different `sheet_name` values.

- **Book lookup:** ISBN (`isbn_13` first, then `isbn_10`).
- **Sale format:** `"print"`.
- **Key validation:** `Units Refunded` must be `0`.
- **Required columns:** `Title`, `Author`, `ISBN`, `Marketplace`, `Units Sold`, `Units Refunded`, `Currency`, `Royalty`.

---

### `_ebook_handler.py` — `_EBookRoyaltySheetHandler`

Handles the **"eBook Royalty"** sheet.

- **Book lookup:** Amazon ebook ASIN (`amazon_asin_ebook` field on `Book`).
- **Sale format:** `"ebook"`.
- **Key validation:** `Units Refunded` must be `0`; `Units Sold` must equal `Net Units Sold`.
- **Required columns:** `Title`, `Author`, `ASIN`, `Marketplace`, `Units Sold`, `Units Refunded`, `Net Units Sold`, `Currency`, `Royalty`.

---

### `_kenp_handler.py` — `_KENPSheetHandler`

Handles the **"KENP"** sheet (Kindle Edition Normalized Pages — Kindle Unlimited revenue).

- **Book lookup:** `eBook ASIN` column.
- **Sale format:** `"kindle unlimited"`.
- **Audiobook rows:** rows where `eBook ASIN == "N/A"` are **skipped with a warning** (non-blocking). These are Audible rows that Amazon bundles into the KENP sheet.
- **quantity vs kenp:** KU rows have no unit quantity. `quantity` is `null`; `kenp` is populated from the `"Kindle Edition Normalized Pages (KENP)"` column.
- **Required columns:** `Title`, `Author`, `eBook ASIN`, `Marketplace`, `Kindle Edition Normalized Pages (KENP)`, `Currency`, `Royalty`.

---

### `_audiobook_handler.py` — `_AudiobookRoyaltySheetHandler`

Handles the **"Audiobook Royalty"** sheet.

Audiobook import is **not supported**. This handler exists only to detect
whether the sheet has data rows and emit a **non-blocking warning** if so.
It never produces preview rows or blocking errors.

---

### `_parser.py` — `AmazonXLSXParser` and the handler registry

Contains:

- **`_SHEET_HANDLERS`** — the ordered list of handler instances the parser
  iterates over. Order is: Paperback → Hardcover → eBook → KENP → Audiobook.
  Only handlers whose `sheet_name` is present in the workbook are invoked.

- **`_SUPPORTED_DATA_SHEET_NAMES`** — the set of sheet names that count as
  "real data". The parser rejects the file early if none of these are present.

- **`AmazonXLSXParser`** — the public parser class. Inherits from
  `SalesImportParser` (in `base_parser.py`). Responsibilities:
  1. Open the XLSX with `openpyxl`.
  2. Check at least one supported data sheet is present.
  3. Dispatch each present sheet to its handler via `parse_rows`.
  4. Merge all `preview_rows`, `errors`, and `warnings` into a single `ParseResult`.

  Holds a `CurrencyConverter` instance at `self._converter`, which sheet
  handlers access via `parser._converter.to_usd(amount, currency)`.

---

## Data flow

```
UploadedFile
    │
    ▼
AmazonXLSXParser.parse_and_validate()
    │  opens XLSX, checks for supported sheets
    │
    ├── _PrintRoyaltySheetHandler.parse_rows()   [Paperback Royalty]
    ├── _PrintRoyaltySheetHandler.parse_rows()   [Hardcover Royalty]
    ├── _EBookRoyaltySheetHandler.parse_rows()   [eBook Royalty]
    ├── _KENPSheetHandler.parse_rows()           [KENP]
    └── _AudiobookRoyaltySheetHandler.parse_rows()[Audiobook Royalty]
            │
            │  each handler:
            │    1. _extract_header()  → (month, year), col_map
            │    2. _check_required_cols()
            │    3. per-row: validate → lookup book → _convert_royalty()
            │    4. _validate_with_serializer()  (via parser)
            │    5. build preview row dict
            │
            ▼
    (preview_rows, errors, warnings) merged across all sheets
            │
            ▼
        ParseResult
```

---

## Adding a new sheet type

1. Create `_mysheet_handler.py` with a class extending `_SheetHandler`.
2. Implement `parse_rows` — call `_extract_header`, `_check_required_cols`,
   iterate rows, call `_convert_royalty`, call `parser._validate_with_serializer`,
   build and append preview row dicts.
3. Add the new handler instance to `_SHEET_HANDLERS` in `_parser.py`.
4. If the sheet contains real sale data, add its name to `_SUPPORTED_DATA_SHEET_NAMES`.
