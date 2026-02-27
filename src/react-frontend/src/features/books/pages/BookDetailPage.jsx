// src/features/books/pages/BookDetailPage.jsx
import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Card,
  CardContent,
  CardHeader,
  Input,
  Button,
  MonthPicker,
  ErrorAlert,
  StatCard,
  DetailField,
  FormField,
  Pagination,
  ShowAllToggle,
  SaleEntryRow,
} from "../../../shared/components";
import { DeleteBookDialog, AuthorsEditor } from "../components";
import SalesTable from "../../sales/components/SalesTable";
import { BOOK_DETAIL_COLUMNS } from "../../sales/config/salesTableConfig";
import { errorMessage } from "../../../shared/utils/errors";
import * as booksApi from "../api/booksApi";
import { useBookSales } from "../hooks/useBookSales";
import { EMPTY_ROW, transformRowToSaleData, isRowComplete } from "../../../shared/utils/salesUtils";
import { createManySales } from "../../sales/api/salesApi";
import { formatMonthYear } from "../../../shared/utils/dateUtils";

function normalizeName(s) {
  return (s || "").trim().replace(/\s+/g, " ");
}

function monthInputFromDate(dateStr) {
  return dateStr || "";
}

function pct(x) {
  const n = Number(x);
  if (Number.isNaN(n)) return "—";
  return `${(n * 100).toFixed(1)}%`;
}

function formatMoney(x) {
  return `$${Number(x || 0).toFixed(2)}`;
}

export default function BookDetailPage() {
  const { bookId } = useParams();
  const nav = useNavigate();

  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [book, setBook] = useState(null);

  // Edit mode
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);

  // Delete dialog
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Form state
  const [title, setTitle] = useState("");
  const [publicationMonth, setPublicationMonth] = useState("");
  const [isbn13, setIsbn13] = useState("");
  const [isbn10, setIsbn10] = useState("");
  const [authors, setAuthors] = useState([{ author_name: "", royalty_rate: "0.50" }]);

  // Authors list for dropdown
  const [authorOptions, setAuthorOptions] = useState([]);
  const [authorsLoading, setAuthorsLoading] = useState(true);
  const [openAuthorIdx, setOpenAuthorIdx] = useState(null);

  // Paginated sales
  const {
    sales: bookSales,
    loading: salesLoading,
    ordering: salesOrdering,
    handleSort: handleSalesSort,
    refresh: refreshSales,
    page: salesPage,
    totalPages: salesTotalPages,
    setPage: setSalesPage,
    count: salesCount,
    showAll: salesShowAll,
    toggleShowAll: toggleSalesShowAll,
  } = useBookSales(bookId);

  // Totals from backend
  const [totalsLoading, setTotalsLoading] = useState(true);
  const [totalsErr, setTotalsErr] = useState(null);
  const [totals, setTotals] = useState({
    publisher_revenue: "0",
    total_royalties: "0",
    paid_royalties: "0",
    unpaid_royalties: "0",
  });

  // Inline sale entry
  const [showSaleEntry, setShowSaleEntry] = useState(false);
  const [saleRow, setSaleRow] = useState({ ...EMPTY_ROW });
  const [saleSubmitting, setSaleSubmitting] = useState(false);
  const [saleError, setSaleError] = useState(null);

  const fixedBook = book
    ? {
        value: book.id,
        label: book.title,
        authors: book.authors,
        publication_date: book.publication_date,
      }
    : null;

  const handleSaleRowChange = (index, field, value) => {
    setSaleRow((prev) => {
      if (typeof field === "object" && field !== null) {
        return { ...prev, ...field };
      }
      return { ...prev, [field]: value };
    });
  };

  async function refreshBook() {
    try {
      const b = await booksApi.getBook(bookId);
      setBook(b);
    } catch (e) {
      console.error("Error refreshing book:", e);
    }
  }

  async function refreshTotals() {
    if (!bookId) return;
    setTotalsLoading(true);
    setTotalsErr(null);
    try {
      const t = await booksApi.getBookSalesTotals(bookId);
      setTotals(t);
    } catch (e) {
      setTotalsErr(errorMessage(e));
    } finally {
      setTotalsLoading(false);
    }
  }

  const handleSubmitSale = async () => {
    setSaleError(null);

    if (!isRowComplete(saleRow)) {
      setSaleError("Please fill in all fields.");
      return;
    }

    setSaleSubmitting(true);
    try {
      const saleData = transformRowToSaleData(saleRow);
      await createManySales([saleData]);

      setSaleRow({ ...EMPTY_ROW });
      setShowSaleEntry(false);

      refreshBook();
      refreshSales();
      refreshTotals();
    } catch (e) {
      setSaleError(errorMessage(e));
    } finally {
      setSaleSubmitting(false);
    }
  };

  const handleCancelSale = () => {
    setSaleRow({ ...EMPTY_ROW });
    setSaleError(null);
    setShowSaleEntry(false);
  };

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setErr(null);
      setAuthorsLoading(true);

      try {
        const [b, a] = await Promise.all([
          booksApi.getBook(bookId),
          booksApi.listAuthors().catch(() => []),
        ]);

        if (cancelled) return;

        setBook(b);
        setTitle(b?.title || "");
        setPublicationMonth(monthInputFromDate(b?.publication_date));
        setIsbn13(b?.isbn_13 || "");
        setIsbn10(b?.isbn_10 || "");

        const initialAuthors =
          (b?.authors || []).length > 0
            ? b.authors.map((x) => ({
                author_name: x.name || "",
                royalty_rate: String(x.royalty_rate ?? "0.50"),
              }))
            : [{ author_name: "", royalty_rate: "0.50" }];

        setAuthors(initialAuthors);
        setAuthorOptions(Array.isArray(a) ? a : []);
      } catch (e) {
        if (!cancelled) setErr(errorMessage(e));
      } finally {
        if (!cancelled) setLoading(false);
        if (!cancelled) setAuthorsLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [bookId]);

  useEffect(() => {
    refreshTotals();
  }, [bookId]);

  function resetFormToBook(b) {
    if (!b) return;
    setTitle(b.title || "");
    setPublicationMonth(monthInputFromDate(b.publication_date));
    setIsbn13(b.isbn_13 || "");
    setIsbn10(b.isbn_10 || "");
    setAuthors(
      (b.authors || []).length > 0
        ? b.authors.map((x) => ({
            author_name: x.name || "",
            royalty_rate: String(x.royalty_rate ?? "0.50"),
          }))
        : [{ author_name: "", royalty_rate: "0.50" }]
    );
  }

  async function onSave() {
    setErr(null);
    setSaving(true);

    try {
      const cleanedAuthors = authors.map((r) => ({
        author_name: normalizeName(r.author_name),
        royalty_rate: String(r.royalty_rate).trim(),
      }));

      const payload = {
        title: title.trim(),
        publication_date: publicationMonth,
        isbn_13: isbn13.replaceAll("-", "").trim(),
        isbn_10: isbn10.trim() === "" ? null : isbn10.replaceAll("-", "").trim(),
        authors: cleanedAuthors,
      };

      const updated = await booksApi.updateBook(bookId, payload);

      setBook(updated);
      setEditing(false);
      resetFormToBook(updated);

      try {
        const a = await booksApi.listAuthors();
        setAuthorOptions(Array.isArray(a) ? a : []);
      } catch {
        // ignore
      }
    } catch (e) {
      setErr(errorMessage(e));
    } finally {
      setSaving(false);
    }
  }

  function onDeleteClick() {
    setErr(null);
    setDeleteOpen(true);
  }

  async function onConfirmDelete() {
    setErr(null);
    setDeleting(true);
    try {
      await booksApi.deleteBook(bookId);
      nav("/books", { replace: true });
    } catch (e) {
      setErr(errorMessage(e));
    } finally {
      setDeleting(false);
      setDeleteOpen(false);
    }
  }

  if (loading) {
    return (
      <div className="p-6">
        <div className="text-slate-600">Loading…</div>
      </div>
    );
  }

  if (!book) {
    return (
      <div className="p-6">
        <div className="text-slate-700">Book not found.</div>
        {err && <div className="mt-2 text-sm text-red-600">{err}</div>}
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-start justify-center p-6">
      <div className="w-full max-w-6xl">
        {/* Book Details Card */}
        <Card>
          <CardHeader
            title={editing ? "Edit Book" : "Book Details"}
            subtitle={editing ? "Update fields and save changes." : "View book metadata and authors."}
          />
          <CardContent>
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                {!editing ? (
                  <>
                    <Button variant="secondary" onClick={() => setEditing(true)}>
                      Edit
                    </Button>
                    <Button variant="danger" onClick={onDeleteClick}>
                      Delete
                    </Button>
                  </>
                ) : (
                  <>
                    <Button
                      variant="secondary"
                      onClick={() => {
                        resetFormToBook(book);
                        setEditing(false);
                      }}
                    >
                      Cancel
                    </Button>
                    <Button disabled={saving} onClick={onSave}>
                      {saving ? "Saving..." : "Save"}
                    </Button>
                  </>
                )}
              </div>
            </div>

            {err && <ErrorAlert className="mt-4">{err}</ErrorAlert>}

            {!editing ? (
              /* View Mode */
              <div className="mt-6 space-y-4">
                <DetailField label="Title">{book.title}</DetailField>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <DetailField label="Publication">
                    {formatMonthYear(book.publication_date)}
                  </DetailField>
                  <DetailField label="Total Sales">{book.total_sales_to_date ?? 0}</DetailField>
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <DetailField label="ISBN-13">
                    <span className="font-mono">{book.isbn_13 || "—"}</span>
                  </DetailField>
                  <DetailField label="ISBN-10">
                    <span className="font-mono">{book.isbn_10 || "—"}</span>
                  </DetailField>
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <DetailField label="Authors">
                    {(book.authors || []).length === 0 ? (
                      "—"
                    ) : (
                      <div className="mt-2 space-y-1">
                        {book.authors.map((a) => (
                          <div key={a.author_id}>{a.name}</div>
                        ))}
                      </div>
                    )}
                  </DetailField>

                  <DetailField label="Royalty Rate">
                    {(book.authors || []).length === 0 ? (
                      "—"
                    ) : (
                      <div className="mt-2 space-y-1">
                        {book.authors.map((a) => (
                          <div key={a.author_id}>{pct(a.royalty_rate)}</div>
                        ))}
                      </div>
                    )}
                  </DetailField>
                </div>
              </div>
            ) : (
              /* Edit Mode */
              <div className="mt-6 space-y-5">
                <FormField label="Title">
                  <Input value={title} onChange={(e) => setTitle(e.target.value)} />
                </FormField>

                <MonthPicker
                  label="Publication month, year"
                  value={publicationMonth}
                  onChange={setPublicationMonth}
                  required
                />

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <FormField label="ISBN-13">
                    <Input value={isbn13} onChange={(e) => setIsbn13(e.target.value)} />
                  </FormField>

                  <FormField label="ISBN-10 (optional)">
                    <Input value={isbn10} onChange={(e) => setIsbn10(e.target.value)} />
                  </FormField>
                </div>

                <AuthorsEditor
                  authors={authors}
                  setAuthors={setAuthors}
                  authorOptions={authorOptions}
                  authorsLoading={authorsLoading}
                  openAuthorIdx={openAuthorIdx}
                  setOpenAuthorIdx={setOpenAuthorIdx}
                />
              </div>
            )}
          </CardContent>
        </Card>

        <DeleteBookDialog
          open={deleteOpen}
          book={book}
          deleting={deleting}
          onCancel={() => {
            if (deleting) return;
            setDeleteOpen(false);
          }}
          onConfirm={onConfirmDelete}
        />

        {/* Sales Records Section */}
        <Card className="mt-8">
          <CardHeader title="Sales Records" subtitle="All sales records for this book." />
          <CardContent>
            <div className="mb-4 flex justify-end">
              {!showSaleEntry && <Button onClick={() => setShowSaleEntry(true)}>Add Sale</Button>}
            </div>

            {showSaleEntry && (
              <div className="mb-6">
                {saleError && <ErrorAlert className="mb-4">{saleError}</ErrorAlert>}

                <SaleEntryRow
                  index={0}
                  data={saleRow}
                  onChange={handleSaleRowChange}
                  onRemove={() => {}}
                  isFirst={true}
                  fixedBook={fixedBook}
                />

                <div className="mt-4 flex justify-end gap-2">
                  <Button variant="secondary" onClick={handleCancelSale} disabled={saleSubmitting}>
                    Cancel
                  </Button>
                  <Button onClick={handleSubmitSale} disabled={saleSubmitting}>
                    {saleSubmitting ? "Submitting..." : "Submit Sale"}
                  </Button>
                </div>
              </div>
            )}

            {totalsErr && <ErrorAlert className="mb-4">{totalsErr}</ErrorAlert>}

            {/* Stats Cards */}
            <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
              <StatCard
                label="Publisher Revenue"
                value={formatMoney(totals.publisher_revenue)}
                loading={totalsLoading}
              />
              <StatCard
                label="Total Royalties"
                value={formatMoney(totals.total_royalties)}
                loading={totalsLoading}
              />
              <StatCard
                label="Paid Royalties"
                value={formatMoney(totals.paid_royalties)}
                loading={totalsLoading}
                variant="success"
              />
              <StatCard
                label="Unpaid Royalties"
                value={formatMoney(totals.unpaid_royalties)}
                loading={totalsLoading}
                variant="danger"
              />
            </div>

            <div className="mb-3 flex items-center justify-end">
              <ShowAllToggle showAll={salesShowAll} onToggle={toggleSalesShowAll} />
            </div>

            <SalesTable
              data={bookSales}
              loading={salesLoading}
              ordering={salesOrdering}
              onSort={handleSalesSort}
              columns={BOOK_DETAIL_COLUMNS}
            />

            {!salesShowAll && (
              <div className="mt-4">
                <Pagination
                  page={salesPage}
                  totalPages={salesTotalPages}
                  onPrev={() => setSalesPage((p) => Math.max(1, p - 1))}
                  onNext={() => setSalesPage((p) => Math.min(salesTotalPages, p + 1))}
                />
              </div>
            )}

            <div className="mt-2 text-sm text-slate-600">
              {salesLoading ? (
                "Loading…"
              ) : (
                <>
                  <span className="font-semibold text-slate-900">{salesCount}</span> sale
                  {salesCount === 1 ? "" : "s"} for this book
                </>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
