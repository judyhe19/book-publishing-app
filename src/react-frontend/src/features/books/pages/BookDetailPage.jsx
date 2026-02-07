// src/features/books/pages/BookDetailPage.jsx
import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Card, CardContent, CardHeader } from "../../../shared/components/Card";
import { Input } from "../../../shared/components/Input";
import { Button } from "../../../shared/components/Button";
import { errorMessage } from "../../../shared/utils/errors";
import * as booksApi from "../api/booksApi";
import { DeleteBookDialog } from "../components/DeleteBookDialog";
import { AuthorsEditor } from "../components/AuthorsEditor";
import { useBookSales } from "../hooks/useBookSales";
import BookSalesTable from "../components/BookSalesTable";
import SaleEntryRow from "../../../shared/components/SaleEntryRow";
import { EMPTY_ROW, transformRowToSaleData, isRowComplete } from "../../../shared/utils/salesUtils";
import { createManySales } from "../../sales/api/salesApi";
import SalesPagination from "../../sales/components/SalesPagination";

function normalizeName(s) {
  return (s || "").trim().replace(/\s+/g, " ");
}

function monthInputFromDate(dateStr) {
  if (!dateStr) return "";
  const m = /^(\d{4})-(\d{2})-\d{2}$/.exec(dateStr);
  return m ? `${m[1]}-${m[2]}` : "";
}

function formatMonthYear(dateStr) {
  if (!dateStr) return "—";
  const m = /^(\d{4})-(\d{2})-\d{2}$/.exec(dateStr);
  if (!m) return dateStr;
  const year = m[1];
  const month = Number(m[2]);
  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
  ];
  return `${monthNames[month - 1]} ${year}`;
}

function pct(x) {
  const n = Number(x);
  if (Number.isNaN(n)) return "—";
  return `${(n * 100).toFixed(1)}%`;
}

export default function BookDetailPage() {
  const { bookId } = useParams();
  const nav = useNavigate();

  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  const [book, setBook] = useState(null);

  // edit mode
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);

  // delete dialog
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // form state
  const [title, setTitle] = useState("");
  const [publicationMonth, setPublicationMonth] = useState(""); // YYYY-MM
  const [isbn13, setIsbn13] = useState("");
  const [isbn10, setIsbn10] = useState("");
  const [authors, setAuthors] = useState([{ author_name: "", royalty_rate: "0.50" }]);

  // authors list for dropdown
  const [authorOptions, setAuthorOptions] = useState([]);
  const [authorsLoading, setAuthorsLoading] = useState(true);
  const [openAuthorIdx, setOpenAuthorIdx] = useState(null);

  // ✅ paginated sales + show-all toggle
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

  // ✅ totals from backend endpoint
  const [totalsLoading, setTotalsLoading] = useState(true);
  const [totalsErr, setTotalsErr] = useState(null);
  const [totals, setTotals] = useState({
    publisher_revenue: "0",
    total_royalties: "0",
    paid_royalties: "0",
    unpaid_royalties: "0",
  });

  // inline sale entry
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

  // ✅ load totals when book changes
  useEffect(() => {
    refreshTotals();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bookId]);

  // Refetch when page regains focus
  useEffect(() => {
    const handleFocus = () => {
      refreshBook();
      refreshSales();
      refreshTotals();
    };

    window.addEventListener("focus", handleFocus);
    return () => window.removeEventListener("focus", handleFocus);
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

      if (!title.trim()) throw new Error("Title is required.");
      if (!publicationMonth) throw new Error("Publication month/year is required.");

      for (const r of cleanedAuthors) {
        if (!r.author_name) throw new Error("Each author must have a name.");
        if (!r.royalty_rate) throw new Error("Each author must have a royalty rate.");
      }

      const nameSet = new Set(cleanedAuthors.map((r) => r.author_name.toLowerCase()));
      if (nameSet.size !== cleanedAuthors.length) {
        throw new Error("Please don’t enter the same author more than once.");
      }

      const byName = new Map(authorOptions.map((a) => [normalizeName(a.name).toLowerCase(), a]));

      const resolvedAuthors = [];
      for (const r of cleanedAuthors) {
        const key = r.author_name.toLowerCase();
        let found = byName.get(key);

        if (!found) {
          found = await booksApi.createAuthor(r.author_name);
          byName.set(key, found);
          setAuthorOptions((prev) => {
            const exists = prev.some((x) => x.id === found.id);
            const next = exists ? prev : [...prev, found];
            return next.sort((x, y) => x.name.localeCompare(y.name));
          });
        }

        resolvedAuthors.push({ author_id: found.id, royalty_rate: r.royalty_rate });
      }

      const payload = {
        title: title.trim(),
        publication_date: `${publicationMonth}-01`,
        isbn_13: isbn13.replaceAll("-", "").trim(),
        isbn_10: isbn10.trim() === "" ? null : isbn10.replaceAll("-", "").trim(),
        authors: resolvedAuthors,
      };

      const updated = await booksApi.updateBook(bookId, payload);
      setBook(updated);
      setEditing(false);
      resetFormToBook(updated);
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
        {err ? <div className="mt-2 text-sm text-red-600">{err}</div> : null}
        <div className="mt-4">
          <Button variant="secondary" onClick={() => nav("/books")}>Back</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-start justify-center p-6">
      <div className="w-full max-w-6xl">
        <Card>
          <CardHeader
            title={editing ? "Edit Book" : "Book Details"}
            subtitle={editing ? "Update fields and save changes." : "View book metadata and authors."}
          />
          <CardContent>
            <div className="flex items-center justify-between gap-2">
              <Button variant="secondary" onClick={() => nav("/books")}>Back</Button>

              <div className="flex items-center gap-2">
                {!editing ? (
                  <>
                    <Button variant="secondary" onClick={() => setEditing(true)}>Edit</Button>
                    <Button onClick={onDeleteClick}>Delete</Button>
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

            {err ? (
              <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {err}
              </div>
            ) : null}

            {!editing ? (
              <div className="mt-6 space-y-4">
                <div>
                  <div className="text-xs font-semibold uppercase text-slate-500">Title</div>
                  <div className="text-slate-900">{book.title}</div>
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div>
                    <div className="text-xs font-semibold uppercase text-slate-500">Publication</div>
                    <div className="text-slate-900">{formatMonthYear(book.publication_date)}</div>
                  </div>
                  <div>
                    <div className="text-xs font-semibold uppercase text-slate-500">Total Sales</div>
                    <div className="text-slate-900">{book.total_sales_to_date ?? 0}</div>
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div>
                    <div className="text-xs font-semibold uppercase text-slate-500">ISBN-13</div>
                    <div className="font-mono text-slate-900">{book.isbn_13 || "—"}</div>
                  </div>
                  <div>
                    <div className="text-xs font-semibold uppercase text-slate-500">ISBN-10</div>
                    <div className="font-mono text-slate-900">{book.isbn_10 || "—"}</div>
                  </div>
                </div>

                {/* ✅ Authors + Royalty Rate aligned like other 2-col fields */}
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div>
                    <div className="text-xs font-semibold uppercase text-slate-500">Authors</div>
                    {(book.authors || []).length === 0 ? (
                      <div className="text-slate-500">—</div>
                    ) : (
                      <div className="mt-2 space-y-1">
                        {book.authors.map((a) => (
                          <div key={a.author_id} className="text-slate-900">
                            {a.name}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div>
                    <div className="text-xs font-semibold uppercase text-slate-500">Royalty Rate</div>
                    {(book.authors || []).length === 0 ? (
                      <div className="text-slate-500">—</div>
                    ) : (
                      <div className="mt-2 space-y-1">
                        {book.authors.map((a) => (
                          <div key={a.author_id} className="text-slate-900">
                            {pct(a.royalty_rate)}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="mt-6 space-y-5">
                <div>
                  <label className="text-sm font-medium text-slate-700">Title</label>
                  <div className="mt-1">
                    <Input value={title} onChange={(e) => setTitle(e.target.value)} />
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium text-slate-700">Publication month, year</label>
                  <div className="mt-1">
                    <input
                      type="month"
                      className="w-full rounded-xl border border-slate-200 px-3 py-2"
                      value={publicationMonth}
                      onChange={(e) => setPublicationMonth(e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div>
                    <label className="text-sm font-medium text-slate-700">ISBN-13</label>
                    <div className="mt-1">
                      <Input value={isbn13} onChange={(e) => setIsbn13(e.target.value)} />
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-slate-700">ISBN-10 (optional)</label>
                    <div className="mt-1">
                      <Input value={isbn10} onChange={(e) => setIsbn10(e.target.value)} />
                    </div>
                  </div>
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
              {!showSaleEntry ? <Button onClick={() => setShowSaleEntry(true)}>Add Sale</Button> : null}
            </div>

            {showSaleEntry && (
              <div className="mb-6">
                {saleError && (
                  <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 whitespace-pre-wrap">
                    {saleError}
                  </div>
                )}

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

            {totalsErr ? (
              <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {totalsErr}
              </div>
            ) : null}

            <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <div className="text-xs font-semibold uppercase text-slate-500">Publisher Revenue</div>
                <div className="mt-1 text-lg font-semibold text-slate-900">
                  {totalsLoading ? "Loading…" : `$${Number(totals.publisher_revenue || 0).toFixed(2)}`}
                </div>
              </div>

              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <div className="text-xs font-semibold uppercase text-slate-500">Total Royalties</div>
                <div className="mt-1 text-lg font-semibold text-slate-900">
                  {totalsLoading ? "Loading…" : `$${Number(totals.total_royalties || 0).toFixed(2)}`}
                </div>
              </div>

              <div className="rounded-lg border border-green-200 bg-green-50 p-4">
                <div className="text-xs font-semibold uppercase text-green-600">Paid Royalties</div>
                <div className="mt-1 text-lg font-semibold text-green-700">
                  {totalsLoading ? "Loading…" : `$${Number(totals.paid_royalties || 0).toFixed(2)}`}
                </div>
              </div>

              <div className="rounded-lg border border-red-200 bg-red-50 p-4">
                <div className="text-xs font-semibold uppercase text-red-600">Unpaid Royalties</div>
                <div className="mt-1 text-lg font-semibold text-red-700">
                  {totalsLoading ? "Loading…" : `$${Number(totals.unpaid_royalties || 0).toFixed(2)}`}
                </div>
              </div>
            </div>

            {/* ✅ Show all / Paginate toggle for THIS book's sales */}
            <div className="mb-3 flex items-center justify-end">
              <Button variant="secondary" onClick={toggleSalesShowAll}>
                {salesShowAll ? "Paginate" : "Show all"}
              </Button>
            </div>

            <BookSalesTable
              data={bookSales}
              loading={salesLoading}
              ordering={salesOrdering}
              onSort={handleSalesSort}
            />

            {/* ✅ pagination controls only when paginating */}
            {!salesShowAll ? (
              <div className="mt-4">
                <SalesPagination
                  page={salesPage}
                  totalPages={salesTotalPages}
                  onPrev={() => setSalesPage((p) => Math.max(1, p - 1))}
                  onNext={() => setSalesPage((p) => Math.min(salesTotalPages, p + 1))}
                />
              </div>
            ) : null}

            <div className="mt-2 text-sm text-slate-600">
              {salesLoading ? (
                "Loading…"
              ) : (
                <>
                  <span className="font-semibold text-slate-900">{salesCount}</span>{" "}
                  sale{salesCount === 1 ? "" : "s"} for this book
                </>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
