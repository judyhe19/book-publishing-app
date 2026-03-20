# TODO: Changes Needed to Fully Utilize the Parser Infrastructure

The `SalesImportParser` base class and `AmazonXLSXParser` skeleton are in place, but several
changes across the backend and frontend are required before Amazon XLSX import is usable.
The Ingram CSV import flow is fully functional today and does not require these changes.

---

## 1. Install `openpyxl` dependency

`AmazonXLSXParser` calls `openpyxl.load_workbook(...)`. This library is not yet listed as a
project dependency.

- Add `openpyxl` to `requirements.txt` (or `pyproject.toml` / `Pipfile`, whichever is in use).
- Run `pip install openpyxl` in the backend virtual environment.

---

## 2. Extend the `Sale` model (`bookapp/models.py`)

The current `Sale` model records only the essentials. Amazon sales introduce new concepts that
need their own fields. Note: `IngramSparkCSVParser` already produces `distributor`, `format`,
and `currency` in its preview rows — the model just needs to catch up.

| New field | Type | Notes |
|---|---|---|
| `distributor` | `CharField(max_length=100, blank=True, null=True)` | e.g. `"Ingram Spark"`, `"Amazon"`, `"Other"`. Null means handsold or not recorded. |
| `format` | `CharField(max_length=30, choices=...)` | `"print"`, `"ebook"`, `"kindle unlimited"`. Default `"print"`. |
| `currency` | `CharField(max_length=3, default="USD")` | ISO 4217 code (e.g. `"USD"`, `"GBP"`, `"EUR"`). |
| `publisher_revenue_original` | `DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)` | Revenue in the original (pre-conversion) currency. Null for USD-only sources like Ingram. |
| `kenp` | `PositiveIntegerField(blank=True, null=True)` | Kindle Edition Normalized Pages read. Only set for `format="kindle unlimited"` rows. Quantity is null for these rows. |

After adding these fields, run:
```
python manage.py makemigrations bookapp --name="sale_distributor_format_currency_kenp"
python manage.py migrate
```

---

## 3. Update `SaleWriteSerializer` (`bookapp/serializers/sales.py`)

- Add the five new fields to the serializer's `fields` list.
- Add validation rules:
  - `kenp` must be provided (and `quantity` must be null/absent) when `format == "kindle unlimited"`.
  - `quantity` must be provided (and `kenp` must be null/absent) for all other formats.
  - `publisher_revenue_original` is optional; if provided, `currency` should also be set.
- `distributor` should be optional (handsold sales have no distributor).
- Update the auto-calculation logic: handsold revenue computation is unaffected, but ensure
  the new fields don't interfere with existing validation paths.

Also update `SaleSerializer` (read serializer) to expose the new fields in API responses.

---

## 4. Implement `_SheetHandler.parse_rows` in `amazon_xlsx.py`

Each of the four sheet handlers has a `parse_rows` method stub that raises `NotImplementedError`.
These need to be filled in:

- **`_PrintRoyaltySheetHandler`** — read "Paperback Royalty" / "Hardcover Royalty":
  - Extract month/year from special first row (cell A1 = `"Sales Period"`, cell B1 = `"June 2025"`).
  - Validate expected columns are present (order may vary, unlike Ingram).
  - For each data row: validate `Units Refunded == 0`, look up book by ISBN, call `parser._converter.to_usd(royalty, currency)`, build preview row with `format="print"`.

- **`_EBookRoyaltySheetHandler`** — read "eBook Royalty":
  - Same first-row month/year extraction.
  - Look up book by ASIN instead of ISBN.
  - Validate `Units Refunded == 0` and `Units Sold == Net Units Sold`.
  - Build preview row with `format="ebook"`.

- **`_KENPSheetHandler`** — read "KENP":
  - Rows where `eBook ASIN == "N/A"` are skipped with a warning (audiobook/Audible rows).
  - For supported rows, `kenp` is populated from `"Kindle Edition Normalized Pages (KENP)"` column; `quantity` is null.
  - Look up book by `eBook ASIN`.
  - Build preview row with `format="kindle unlimited"`.

- **`_AudiobookRoyaltySheetHandler`** — read "Audiobook Royalty":
  - Not imported. Verify no data rows are present.
  - If data rows exist, emit a warning (non-blocking) so the user is informed.

All handlers build preview rows using `parser._converter.to_usd(royalty, currency)` for the
USD revenue and include `distributor=parser.DISTRIBUTOR_NAME`, `format`, and `currency` in
every preview row dict.

---

## 5. Add `import_amazon_xlsx` view action (`bookapp/views/sales.py`)

Following the `import_ingram_csv` action as a template:

- Accept a multipart POST with the XLSX file.
- Instantiate `AmazonXLSXParser()` and call `.parse_and_validate(file)`.
- On errors: return `{"errors": result.errors, "warnings": result.warnings}` with HTTP 400.
- On success: return `{"preview": result.preview, "warnings": result.warnings, **result.metadata}` with HTTP 200.

---

## 6. Register the new URL (`bookapp/urls.py`)

Add a URL entry for the new `import_amazon_xlsx` action, e.g.:
```
POST /api/sales/import-amazon-xlsx/
```

---

## 7. Add `importAmazonXLSX` to the frontend API client (`salesApi.js`)

A new function analogous to `validateIngramCSV`, but sending the file without month/year parameters.

---

## 8. Build `AmazonXLSXImportPage.jsx` (frontend)

Follow the two-step pattern of `IngramCSVImportPage.jsx`:

**Step 1 — Upload & Validate:**
- File picker (`.xlsx` only).
- "Validate & Preview" button calls the new API function.
- Display any errors as a list; display any warnings distinctly (yellow/amber, non-blocking) with an acknowledgement step before proceeding.

**Step 2 — Preview & Confirm:**
- Show all preview rows (grouped by sheet/format is a nice-to-have).
- Include the new fields: format, distributor, currency, KENP where applicable.
- "Confirm Import" button calls `createManySales`.

---

## 9. Update Sales UI for new fields

Once the `Sale` model has `distributor`, `format`, `currency`, `kenp`:

- **Sales list table** (`salesTableConfig.jsx`): consider adding a Format column or badge.
- **Sales detail/edit view**: expose the new fields so users can correct them if needed.
- **Sales input tool** (`SalesInputPage.jsx`): add distributor, format, currency, and KENP inputs per the requirements (these were already specified in the requirements but not yet implemented).
- **Royalty report / author payments pages**: KENP rows have no quantity; ensure no division or display logic assumes quantity is always present.
