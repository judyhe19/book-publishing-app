// src/features/sales/pages/SalesDetailPage.jsx
import { useState, useEffect, useMemo } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import AsyncSelect from "react-select/async";
import {
  Button,
  ErrorAlert,
  LoadingState,
  PageHeader,
  Input,
  MonthPicker,
} from "../../../shared/components";
import { useBookSearch } from "../../../shared/hooks/useBookSearch";
import { formatBookLabel } from "../../../shared/utils/bookUtils";
import { useSalesDetails } from "../hooks/useSalesDetails";
import { DeleteSalesRecordDialog } from "../components";
import { formatMoney } from "../../../shared/utils/formatUtils";

const selectStyles = {
  menuPortal: (base) => ({ ...base, zIndex: 9999 }),
  control: (base) => ({
    ...base,
    borderRadius: "0.75rem",
    borderColor: "#e2e8f0",
    boxShadow: "none",
    "&:hover": { borderColor: "#e2e8f0" },
  }),
};

const inputClass =
  "w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent bg-white";

export default function SalesDetailPage() {
  const { saleId } = useParams();
  const [searchParams] = useSearchParams();

  const { sale, book, loading, saving, error, save, remove } = useSalesDetails(saleId);

  const [form, setForm] = useState(null);
  const [selectedBook, setSelectedBook] = useState(null);
  const [deleteOpen, setDeleteOpen] = useState(false);

  // Book search hook — filters by sale date
  const { loadOptions } = useBookSearch({ date: form?.date });

  // Initialize form from loaded sale
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => {
    if (!sale || !book) return;
    setForm({
      date: sale.date || "",
      book_id: sale.book,
      format: sale.format ?? "",
      quantity: sale.quantity ?? "",
      kenp: sale.kenp ?? "",
      distributor: sale.distributor ?? "",
      currency: sale.currency ?? "",
      publisher_revenue_original: sale.publisher_revenue_original ?? "",
      publisher_revenue: sale.publisher_revenue || "",
      author_royalty: sale.author_royalty || "",
      author_paid: sale.author_paid || false,
      comment: sale.comment || "",
    });
    setSelectedBook({
      value: book.id,
      label: formatBookLabel(book.title, book.isbn_13, book.amazon_asin_ebook),
      authors: book.authors || [],
      publication_date: book.publication_date,
      distributor_author_royalty_rate: book.distributor_author_royalty_rate,
      hand_sold_author_royalty_rate: book.hand_sold_author_royalty_rate,
      cover_price: book.cover_price,
      print_cost: book.print_cost,
      amazon_asin_ebook: book.amazon_asin_ebook,
    });
  }, [sale, book]);

  const isDistributor = sale?.sale_source === "distributor";
  const isHandsold = sale?.sale_source === "handsold";
  const isKU = form?.format === "kindle unlimited";

  // ---------------------------------------------------------------
  // Auto-calculate author_royalty when publisher_revenue changes
  // author_royalty = royalty_rate × publisher_revenue
  // ---------------------------------------------------------------
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => {
    if (!form || !sale?.sale_source || !selectedBook) return;

    const rate = isHandsold
      ? Number(selectedBook?.hand_sold_author_royalty_rate ?? 0)
      : Number(selectedBook?.distributor_author_royalty_rate ?? 0);
    const revenue = Number(form.publisher_revenue);

    if (Number.isNaN(rate) || Number.isNaN(revenue)) return;

    const computed = (rate * revenue).toFixed(2);

    if (computed !== String(form.author_royalty)) {
      setForm((prev) => ({ ...prev, author_royalty: computed }));
    }
  }, [form?.publisher_revenue, selectedBook, isDistributor, isHandsold, sale?.sale_source]);

  // ---------------------------------------------------------------
  // Auto-convert currency to USD when original revenue or currency changes
  // ---------------------------------------------------------------
  const [currencyError, setCurrencyError] = useState(null);

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => {
    if (!form || !isDistributor || !form.currency || form.currency === "USD") {
      setCurrencyError(null);
      return;
    }

    const amount = Number(form.publisher_revenue_original);
    if (Number.isNaN(amount) || amount <= 0) {
      if (form.publisher_revenue !== "") {
        setForm((prev) => ({ ...prev, publisher_revenue: "" }));
      }
      setCurrencyError(null);
      return;
    }

    const timeoutId = setTimeout(() => {
      import("../api/salesApi").then(({ convertCurrency }) => {
        convertCurrency(amount, form.currency)
          .then((res) => {
            setCurrencyError(null);
            if (res.usd_amount) {
              // Format to 2 decimal places to be consistent with UI
              const formattedUsd = Number(res.usd_amount).toFixed(2);
              if (formattedUsd !== String(form.publisher_revenue)) {
                setForm((prev) => ({ ...prev, publisher_revenue: formattedUsd }));
              }
            }
          })
          .catch((err) => {
            const errorMsg = err.error || err.message || (typeof err === 'string' ? err : "Invalid currency.");
            setCurrencyError(errorMsg);
            setForm((prev) => ({ ...prev, publisher_revenue: "" })); // clear preview
          });
      });
    }, 600); // 600ms debounce

    return () => clearTimeout(timeoutId);
  }, [form?.publisher_revenue_original, form?.currency, isDistributor]);

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleBookChange = (option) => {
    setSelectedBook(option);
    handleChange("book_id", option?.value || null);

    // Recalculate author_royalty for the new book's royalty rate
    if (sale?.sale_source && form) {
      const rate = isHandsold
        ? Number(option?.hand_sold_author_royalty_rate ?? 0)
        : Number(option?.distributor_author_royalty_rate ?? 0);
      const revenue = Number(form.publisher_revenue);
      if (!Number.isNaN(rate) && !Number.isNaN(revenue)) {
        handleChange("author_royalty", (rate * revenue).toFixed(2));
      }
    }
  };

  const handleDateChange = (newDate) => {
    handleChange("date", newDate);
    // Clear book if its publication date is after the new sale date
    if (selectedBook && newDate) {
      const bookPubDate = selectedBook.publication_date;
      if (bookPubDate) {
        const [saleYear, saleMonth] = newDate.split("-").map(Number);
        const [pubYear, pubMonth] = bookPubDate.split("-").map(Number);
        if (pubYear * 100 + pubMonth > saleYear * 100 + saleMonth) {
          setSelectedBook(null);
          handleChange("book_id", null);
        }
      }
    }
  };

  const payload = useMemo(() => {
    if (!form || !form.book_id) return null;
    
    const base = {
      date: form.date,
      book: form.book_id,
      quantity: isKU ? null : Number(form.quantity),
      kenp: isKU ? (Number(form.kenp) || null) : null,
      author_paid: form.author_paid,
      comment: form.comment,
    };

    if (isDistributor) {
      base.currency = form.currency || "USD";
      if (base.currency === "USD") {
        base.publisher_revenue = String(form.publisher_revenue);
        base.publisher_revenue_original = base.publisher_revenue;
      } else {
        base.publisher_revenue_original = String(form.publisher_revenue_original);
        // Do not send publisher_revenue so the backend recalculates it.
      }
    } else {
      base.publisher_revenue = String(form.publisher_revenue);
    }
    
    return base;
  }, [form, isKU, isDistributor]);

  function reloadBack() {
    const returnTo = searchParams.get("returnTo");
    if (returnTo) {
      window.location.href = returnTo;
    } else {
      window.history.back();
    }
  }

  async function onSave() {
    if (!form || !payload) return;
    await save(payload);
    reloadBack();
  }

  async function onConfirmDelete() {
    await remove();
    reloadBack();
  }

  if (loading) {
    return <LoadingState message="Loading sales record..." fullPage />;
  }

  if (!sale) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <ErrorAlert>{error || "Sale not found."}</ErrorAlert>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <PageHeader title="Sales Record" subtitle="View and modify sales record details.">
        <Button variant="danger" onClick={() => setDeleteOpen(true)} disabled={saving}>
          Delete
        </Button>
        <Button onClick={onSave} disabled={saving || !payload}>
          {saving ? "Saving..." : "Save Changes"}
        </Button>
      </PageHeader>

      {error && <ErrorAlert variant="leftBorder" className="mb-4">{error}</ErrorAlert>}

      {form && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-5">

          {/* Book selector (editable) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Book (Title or ISBN)
            </label>
            <AsyncSelect
              cacheOptions
              loadOptions={loadOptions}
              defaultOptions
              onChange={handleBookChange}
              value={selectedBook}
              placeholder="Search..."
              menuPortalTarget={document.body}
              styles={selectStyles}
            />
          </div>

          {/* Read-only info row */}
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[140px]">
              <label className="block text-sm font-medium text-gray-700 mb-1">Author</label>
              <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200">
                {selectedBook?.authors?.[0]?.name || sale.author_names?.[0] || "—"}
              </div>
            </div>
            <div className="w-32">
              <label className="block text-sm font-medium text-gray-700 mb-1">Sale Source</label>
              <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200 capitalize">
                {sale.sale_source || "—"}
              </div>
            </div>
            {form.format && (
              <div className="w-36">
                <label className="block text-sm font-medium text-gray-700 mb-1">Format</label>
                <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200">
                  {{ print: 'Print', ebook: 'eBook', 'kindle unlimited': 'Kindle Unlimited' }[form.format] || form.format}
                </div>
              </div>
            )}
            {form.distributor && (
              <div className="w-36">
                <label className="block text-sm font-medium text-gray-700 mb-1">Distributor</label>
                <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200">
                  {form.distributor}
                </div>
              </div>
            )}
            {isDistributor ? (
              <div className="w-24">
                <label className="block text-sm font-medium text-gray-700 mb-1">Currency</label>
                <Input
                  type="text"
                  maxLength={3}
                  value={form.currency}
                  onChange={(e) => {
                    setCurrencyError(null);
                    handleChange("currency", e.target.value.toUpperCase());
                  }}
                  placeholder="USD"
                  className={currencyError ? "border-red-500 bg-red-50 text-red-900" : ""}
                />
              </div>
            ) : form.currency ? (
              <div className="w-20">
                <label className="block text-sm font-medium text-gray-700 mb-1">Currency</label>
                <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200">
                  {form.currency}
                </div>
              </div>
            ) : null}
          </div>

          {currencyError && (
            <div className="text-red-500 text-sm">{currencyError}</div>
          )}

          {/* Editable fields */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Month/Year</label>
              <MonthPicker
                value={form.date}
                onChange={handleDateChange}
                min={selectedBook?.publication_date || book?.publication_date}
              />
            </div>
            <div>
              {isKU ? (
                <>
                  <label className="block text-sm font-medium text-gray-700 mb-1">KENP</label>
                  <Input
                    type="number"
                    min="1"
                    step="1"
                    value={form.kenp}
                    onChange={(e) => handleChange("kenp", e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "." || e.key === "e" || e.key === "E") {
                        e.preventDefault();
                      }
                    }}
                  />
                </>
              ) : (
                <>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
                  <Input
                    type="number"
                    min="1"
                    step="1"
                    value={form.quantity}
                    onChange={(e) => handleChange("quantity", e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "." || e.key === "e" || e.key === "E") {
                        e.preventDefault();
                      }
                    }}
                  />
                </>
              )}
            </div>
          </div>

          <div className="flex flex-wrap gap-4">
            {/* Publisher Revenue — editable for distributor */}
            <div className="flex-1 min-w-[140px]">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {isDistributor && form.currency && form.currency !== 'USD' ? `Revenue (${form.currency})` : 'Revenue (USD)'}
              </label>
              {isDistributor ? (
                <div className="relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                    <span className="text-gray-500 text-sm">
                      {!form.currency || form.currency === 'USD' ? '$' : form.currency}
                    </span>
                  </div>
                  <Input
                    type="number"
                    step="0.01"
                    className={(!form.currency || form.currency === 'USD') ? "pl-7" : "pl-12"}
                    placeholder="0.00"
                    value={(!form.currency || form.currency === 'USD') ? form.publisher_revenue : (form.publisher_revenue_original ?? '')}
                    onChange={(e) => {
                      if (!form.currency || form.currency === 'USD') {
                        handleChange("publisher_revenue", e.target.value);
                      } else {
                        handleChange("publisher_revenue_original", e.target.value);
                      }
                    }}
                  />
                </div>
              ) : (
                <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200">
                  {formatMoney(form.publisher_revenue, "$0.00")}
                </div>
              )}
            </div>

            {/* Original currency revenue — read-only when non-USD */}
            {isDistributor && form.currency && form.currency !== "USD" && (
              <div className="flex-1 min-w-[140px]">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Revenue (USD)
                </label>
                <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200">
                  {formatMoney(form.publisher_revenue, "$0.00")}
                </div>
              </div>
            )}

            {/* Author Royalty (read-only) */}
            <div className="flex-1 min-w-[140px]">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Author Royalty
              </label>
              <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200">
                {formatMoney(form.author_royalty, "$0.00")}
              </div>
            </div>
          </div>

          {/* Paid checkbox */}
          <div className="flex items-center gap-2">
            <input
              id="author-paid"
              type="checkbox"
              className="form-checkbox h-4 w-4 text-slate-900 rounded border-gray-300 focus:ring-slate-900"
              checked={form.author_paid}
              onChange={(e) => handleChange("author_paid", e.target.checked)}
            />
            <label htmlFor="author-paid" className="text-sm font-medium text-gray-700">
              Author Paid
            </label>
          </div>

          {/* Comment */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Comment</label>
            <textarea
              className={inputClass + " resize-none"}
              rows={3}
              placeholder="Optional comment..."
              value={form.comment}
              onChange={(e) => handleChange("comment", e.target.value)}
            />
          </div>
        </div>
      )}

      <DeleteSalesRecordDialog
        open={deleteOpen}
        onConfirm={onConfirmDelete}
        onCancel={() => setDeleteOpen(false)}
        saleId={sale.id}
        disabled={saving}
      />
    </div>
  );
}