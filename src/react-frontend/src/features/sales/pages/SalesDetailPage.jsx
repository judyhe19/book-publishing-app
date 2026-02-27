// src/features/sales/pages/SalesDetailPage.jsx
import { useState, useEffect, useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
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
  const navigate = useNavigate();

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
      quantity: sale.quantity || "",
      publisher_revenue: sale.publisher_revenue || "",
      author_royalty: sale.author_royalty || "",
      author_paid: sale.author_paid || false,
      comment: sale.comment || "",
    });
    setSelectedBook({
      value: book.id,
      label: formatBookLabel(book.title, book.isbn_13),
      authors: book.authors || [],
      publication_date: book.publication_date,
    });
  }, [sale, book]);

  const isDistributor = sale?.sale_source === "distributor";

  // ---------------------------------------------------------------
  // Auto-calculate author_royalty when publisher_revenue changes
  // for distributor sales: author_royalty = royalty_rate × revenue
  // ---------------------------------------------------------------
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => {
    if (!form || !isDistributor) return;

    // TODO: Once the Book model has a dedicated `distributor_royalty_rate`
    //       field, use that instead of `authors[0].royalty_rate`.
    const royaltyRate = Number(selectedBook?.authors?.[0]?.royalty_rate ?? 0);
    const revenue = Number(form.publisher_revenue);

    if (Number.isNaN(royaltyRate) || Number.isNaN(revenue)) return;

    const computed = (royaltyRate * revenue).toFixed(2);

    if (computed !== String(form.author_royalty)) {
      setForm((prev) => ({ ...prev, author_royalty: computed }));
    }
  }, [form, selectedBook, isDistributor]);

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleBookChange = (option) => {
    setSelectedBook(option);
    handleChange("book_id", option?.value || null);

    // Recalculate author_royalty for the new book's royalty rate
    if (isDistributor && option?.authors?.[0]?.royalty_rate && form) {
      // TODO: Use `option.distributor_royalty_rate` once available
      const rate = Number(option.authors[0].royalty_rate);
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
    return {
      date: form.date,
      book: form.book_id,
      quantity: Number(form.quantity),
      publisher_revenue: String(form.publisher_revenue),
      author_paid: form.author_paid,
      comment: form.comment,
    };
  }, [form]);

  async function onSave() {
    if (!form || !payload) return;
    await save(payload);
    navigate(-1);
  }

  async function onConfirmDelete() {
    await remove();
    navigate(-1);
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
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Author</label>
              <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200">
                {selectedBook?.authors?.[0]?.name || sale.author_names?.[0] || "—"}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Sale Source</label>
              <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200 capitalize">
                {sale.sale_source || "—"}
              </div>
            </div>
          </div>

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
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* Publisher Revenue — only editable for distributor */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Publisher Revenue
              </label>
              {isDistributor ? (
                <div className="relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                    <span className="text-gray-500 text-sm">$</span>
                  </div>
                  <Input
                    type="number"
                    step="0.01"
                    className="pl-7"
                    placeholder="0.00"
                    value={form.publisher_revenue}
                    onChange={(e) => handleChange("publisher_revenue", e.target.value)}
                  />
                </div>
              ) : (
                <div className="text-sm text-slate-900 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200">
                  {formatMoney(form.publisher_revenue, "$0.00")}
                </div>
              )}
            </div>

            {/* Author Royalty (read-only) */}
            <div>
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