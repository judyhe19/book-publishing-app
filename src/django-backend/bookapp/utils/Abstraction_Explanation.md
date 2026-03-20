# Sales Import Parser Abstraction

## Why This Abstraction Exists

Sales data arrives from multiple distributors, each with a different file format and schema. Rather than writing completely independent one-off scripts, the parsers share a common base class so that:

- The rest of the codebase (views, tests, frontend) always deals with the same return type regardless of which distributor's file is being parsed.
- Logic that every parser needs — book lookups, royalty calculation, timestamp capture, decimal rounding, serializer validation — lives in one place and is not duplicated.
- A new parser author only has to think about format-specific concerns (how to open the file, which columns to read, what validations apply) and not about plumbing.

---

## Key Types

### `ParseResult` (dataclass, `base_parser.py`)

Every `parse_and_validate()` call returns a `ParseResult`:

| Field | Type | Meaning |
|---|---|---|
| `preview` | `list[dict]` | Ready-to-import sale rows. **Empty if any errors exist.** |
| `errors` | `list[str]` | Blocking validation errors. User must fix before proceeding. |
| `warnings` | `list[str]` | Non-blocking notices (e.g. unsupported rows skipped). Preview may still be populated. |
| `metadata` | `dict` | At minimum `{"filename": str, "timestamp": str}`. |

`errors` and `preview` are mutually exclusive: a non-empty `errors` list always means an empty `preview`.

### `SalesImportParser` (ABC, `base_parser.py`)

The abstract base class all parsers extend. Subclasses must:

1. Set `DISTRIBUTOR_NAME` as a class-level string constant.
2. Implement `parse_and_validate(self, file, **kwargs) -> ParseResult`.

Everything else is provided as protected helpers (see below).

---

## Protected Helpers (available to all subclasses)

| Method | Purpose |
|---|---|
| `_capture_timestamp()` | Returns `"YYYY-MM-DD HH:MM:SS"` for the current local time. |
| `_money(value)` | Rounds to 2 decimal places (ROUND_HALF_UP). Use for all monetary arithmetic. |
| `_lookup_book_by_isbn(isbn)` | Queries `isbn_13` then `isbn_10`. Returns `Book` or `None`. |
| `_lookup_book_by_asin(asin)` | Queries `amazon_asin_ebook`. Returns `Book` or `None`. |
| `_compute_author_royalty(book, revenue_usd)` | `distributor_author_royalty_rate × revenue_usd`, rounded to 2 dp. |
| `_validate_with_serializer(payload, line_ref)` | Runs `SaleWriteSerializer` on a payload dict. Returns `(validated_data, errors)`. Formats DRF errors with a context prefix like `"Row 5:"` or `"Sheet 'eBook Royalty', row 3:"`. |

The book-lookup helpers intentionally return `None` instead of appending errors. This lets each concrete parser write context-specific messages that include the right location reference (a CSV row number vs. a sheet name + row number).

Currency conversion is **not** a base-class concern. Parsers that need it (i.e. Amazon) own a `CurrencyConverter` instance themselves and call `self._converter.to_usd(amount, currency)`. Parsers that always receive USD (i.e. Ingram) have no converter at all.

---

## Existing Implementations

### `IngramSparkCSVParser` (`ingram_csv.py`)

- `DISTRIBUTOR_NAME = "Ingram Spark"`
- `parse_and_validate(file, *, month, year)` — month/year are **user-provided** (not in the file).
- Reads a flat CSV; stops at the blank row that precedes Ingram's totals footer.
- Validates column names and exact ordering, Returned Qty == 0, Net Qty == Gross Qty, ISBN lookup, and business logic via `SaleWriteSerializer`.
- Uses `_lookup_book_by_isbn` for every row.
- Always USD; no currency conversion needed.
- `warnings` is always `[]`.
- Preview rows include: `distributor` (`self.DISTRIBUTOR_NAME`), `format` (`"print"`), `currency` (`"USD"`), plus all standard sale fields.

### `AmazonXLSXParser` (`amazon_xlsx.py`) *(skeleton — row parsing not yet implemented)*

- `DISTRIBUTOR_NAME = "Amazon"`
- `parse_and_validate(file)` — month/year are **embedded in the file** (per-sheet special first row).
- `__init__` creates `self._converter = CurrencyConverter()`. Sheet handlers call `parser._converter.to_usd(amount, currency)` for non-USD rows.
- Opens the XLSX with `openpyxl`; dispatches each present sheet to a `_SheetHandler`.
- Uses `_lookup_book_by_isbn` for print sheets and `_lookup_book_by_asin` for ebook/KENP sheets.
- May have non-empty `warnings` (unsupported audiobook rows, KENP rows with no ebook ASIN).
- Internal `_SheetHandler` ABC (private to `amazon_xlsx.py`) isolates per-sheet logic. See that file for the four concrete handlers.

---

## How to Add a New Parser

1. **Create a new file** in `bookapp/utils/`, e.g. `my_distributor.py`.

2. **Import the base class:**
   ```python
   from .base_parser import ParseResult, SalesImportParser
   ```

3. **Subclass `SalesImportParser`:**
   ```python
   class MyDistributorParser(SalesImportParser):
       DISTRIBUTOR_NAME = "My Distributor"

       def parse_and_validate(self, file, **kwargs) -> ParseResult:
           filename = file.name or "unknown"
           timestamp = self._capture_timestamp()
           metadata = {"filename": filename, "timestamp": timestamp}

           # ... open and validate the file ...
           # ... for each row, call self._lookup_book_by_isbn(...) etc. ...
           # ... build preview rows ...

           if errors:
               return ParseResult(errors=errors, metadata=metadata)
           return ParseResult(preview=preview_rows, warnings=warnings, metadata=metadata)
   ```

4. **Use the shared helpers** wherever possible rather than re-implementing book lookups, royalty math, or serializer validation.

5. **If your parser handles non-USD currencies**, add `self._converter = CurrencyConverter()` in `__init__` and call `self._converter.to_usd(amount, currency)` when building each preview row. Do not add currency conversion to the base class.

6. **Preview rows must include** `distributor` (use `self.DISTRIBUTOR_NAME`), `format`, and `currency` in addition to the standard sale fields — these are required by the import requirements even if the Sale model doesn't yet have those columns.

7. **Add a new view action** in `bookapp/views/sales.py` (follow the `import_ingram_csv` action as a template). The action should:
   - Accept the uploaded file (and any user-provided parameters).
   - Instantiate the parser and call `parse_and_validate`.
   - Return `{"errors": result.errors}` on failure or `{"preview": result.preview, "warnings": result.warnings, **result.metadata}` on success.

8. **Register the URL** in `bookapp/urls.py`.

9. **Build the frontend import page** following the two-step pattern of `IngramCSVImportPage.jsx` (upload → validate → preview → confirm).

### If your format has multiple sub-schemas (like Amazon's multiple sheets)

Use an internal `_SheetHandler` ABC pattern within your parser module (see `amazon_xlsx.py`). Each sub-schema gets its own handler class; the top-level parser iterates over handlers and merges results. Keep the `_SheetHandler` classes private to the module (prefix with `_`) since they are implementation details, not part of the public interface.
