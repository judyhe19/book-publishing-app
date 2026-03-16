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
import { DeleteBookDialog, BookSalesTable } from "../components";
import { errorMessage } from "../../../shared/utils/errors";
import * as booksApi from "../api/booksApi";
import { useBookSales } from "../hooks/useBookSales";
import { EMPTY_ROW, transformRowToSaleData, isRowComplete } from "../../../shared/utils/salesUtils";
import { createManySales } from "../../sales/api/salesApi";
import { formatMonthYear } from "../../../shared/utils/dateUtils";

// ─── helpers ─────────────────────────────────────────────────────────────────

function pct(x) {
  const n = Number(x);
  if (Number.isNaN(n)) return "—";
  return `${(n * 100).toFixed(1)}%`;
}

function formatMoney(x) {
  return `$${Number(x || 0).toFixed(2)}`;
}

// ─── sub-component: Cover Image ───────────────────────────────────────────────

function CoverImage({ path, title }) {
  const [errored, setErrored] = useState(false);

  if (!path || errored) {
    return (
      <div className="flex h-64 w-48 flex-shrink-0 items-center justify-center rounded-lg border-2 border-dashed border-slate-200 bg-slate-50 text-center text-xs text-slate-400">
        No cover art
      </div>
    );
  }

  return (
    <img
      src={path}
      alt={`Cover of ${title}`}
      className="h-64 w-auto max-w-[12rem] flex-shrink-0 rounded-lg object-cover shadow-md"
      onError={() => setErrored(true)}
    />
  );
}

// ─── sub-component: Series Edit Warning ──────────────────────────────────────
// Shown when the user edits series fields so they know the save is deferred
// if there would be a uniqueness conflict (handled by clearing then re-saving).

function SeriesFields({ seriesName, setSeriesName, seriesPosition, setSeriesPosition }) {
  return (
    <div className="rounded-md border border-amber-200 bg-amber-50 p-4 space-y-3">
      <p className="text-xs text-amber-700">
        <strong>Series editing note:</strong> If swapping positions with another book, first
        clear one book's series fields, save, then assign the new position. This avoids
        uniqueness conflicts.
      </p>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <FormField label="Series name (optional)">
          <Input
            value={seriesName}
            onChange={(e) => setSeriesName(e.target.value)}
            placeholder="e.g. The Lord of the Rings"
          />
        </FormField>
        <FormField label="Series position (optional)">
          <Input
            type="number"
            min="1"
            value={seriesPosition}
            onChange={(e) => setSeriesPosition(e.target.value)}
            placeholder="e.g. 1"
          />
        </FormField>
      </div>
      {/* Clear button */}
      <div>
        <button
          type="button"
          className="text-xs text-slate-500 underline hover:text-red-600"
          onClick={() => {
            setSeriesName("");
            setSeriesPosition("");
          }}
        >
          Clear series fields
        </button>
      </div>
    </div>
  );
}

// ─── main component ───────────────────────────────────────────────────────────

export default function BookDetailPage() {
  const { bookId } = useParams();
  const nav = useNavigate();

  // ── fetch state ──
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [book, setBook] = useState(null);

  // ── edit/delete ui ──
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // ── form state ──
  const [title, setTitle] = useState("");
  const [publicationMonth, setPublicationMonth] = useState("");
  const [isbn13, setIsbn13] = useState("");
  const [isbn10, setIsbn10] = useState("");

  // Single-author fields
  const [authorOptions, setAuthorOptions] = useState([]);
  const [authorsLoading, setAuthorsLoading] = useState(true);
  const [selectedAuthorId, setSelectedAuthorId] = useState("");
  const [authorSearch, setAuthorSearch] = useState("");
  const [authorDropdownOpen, setAuthorDropdownOpen] = useState(false);

  // Royalty / pricing
  const [distributorRoyaltyRate, setDistributorRoyaltyRate] = useState("50");
  const [handSoldRoyaltyRate, setHandSoldRoyaltyRate] = useState("20");
  const [coverPrice, setCoverPrice] = useState("");
  const [printCost, setPrintCost] = useState("");

  // Cover art
  const [coverImagePath, setCoverImagePath] = useState("");

  // Series
  const [seriesName, setSeriesName] = useState("");
  const [seriesPosition, setSeriesPosition] = useState("");

  // ── paginated sales ──
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

  // ── totals ──
  const [totalsLoading, setTotalsLoading] = useState(true);
  const [totalsErr, setTotalsErr] = useState(null);
  const [totals, setTotals] = useState({
    publisher_revenue: "0",
    total_royalties: "0",
    paid_royalties: "0",
    unpaid_royalties: "0",
  });

  // ── inline sale entry ──
  const [showSaleEntry, setShowSaleEntry] = useState(false);
  const [saleRow, setSaleRow] = useState({ ...EMPTY_ROW });
  const [saleSubmitting, setSaleSubmitting] = useState(false);
  const [saleError, setSaleError] = useState(null);

  const fixedBook = book
    ? {
        value: book.id,
        label: book.title,
        publication_date: book.publication_date,
      }
    : null;

  // ── helpers ──

  function populateFormFromBook(b) {
    if (!b) return;
    setTitle(b.title || "");
    setPublicationMonth(b.publication_date || "");
    setIsbn13(b.isbn_13 || "");
    setIsbn10(b.isbn_10 || "");
    setSelectedAuthorId(b.author_id != null ? String(b.author_id) : "");
    setAuthorSearch(b.author_name || "");
    setDistributorRoyaltyRate(String((parseFloat(b.distributor_author_royalty_rate ?? 0.50) * 100)));
    setHandSoldRoyaltyRate(String((parseFloat(b.hand_sold_author_royalty_rate ?? 0.20) * 100)));
    setCoverPrice(b.cover_price != null ? String(b.cover_price) : "");
    setPrintCost(b.print_cost != null ? String(b.print_cost) : "");
    setCoverImagePath(b.cover_image_path || "");
    setSeriesName(b.series_name || "");
    setSeriesPosition(b.series_position != null ? String(b.series_position) : "");
  }

  // ── load ──

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
        populateFormFromBook(b);
        setAuthorOptions(Array.isArray(a) ? a : []);
      } catch (e) {
        if (!cancelled) setErr(errorMessage(e));
      } finally {
        if (!cancelled) {
          setLoading(false);
          setAuthorsLoading(false);
        }
      }
    }

    load();
    return () => { cancelled = true; };
  }, [bookId]);

  useEffect(() => {
    refreshTotals();
  }, [bookId]);

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

  // ── author search dropdown ──

  const filteredAuthors = authorOptions.filter((a) =>
    (a.name || "").toLowerCase().includes(authorSearch.toLowerCase())
  );

  function selectAuthor(a) {
    setSelectedAuthorId(String(a.id));
    setAuthorSearch(a.name);
    setAuthorDropdownOpen(false);
  }

  // ── save ──

  async function onSave() {
    setErr(null);
    setSaving(true);

    try {
      const payload = {
        title: title.trim(),
        publication_date: publicationMonth,
        isbn_13: isbn13.replaceAll("-", "").trim(),
        // Send null to explicitly clear optional fields
        isbn_10: isbn10.trim() === "" ? null : isbn10.replaceAll("-", "").trim(),
        author_id: selectedAuthorId ? Number(selectedAuthorId) : undefined,
        distributor_author_royalty_rate: String(parseFloat(distributorRoyaltyRate) / 100),
        hand_sold_author_royalty_rate: String(parseFloat(handSoldRoyaltyRate) / 100),
        cover_price: coverPrice,
        print_cost: printCost,
        // Explicit null to clear
        cover_image_path: coverImagePath.trim() === "" ? null : coverImagePath.trim(),
        series_name: seriesName.trim() === "" ? null : seriesName.trim(),
        series_position:
          seriesPosition === "" || seriesPosition == null
            ? null
            : Number(seriesPosition),
      };

      const updated = await booksApi.updateBook(bookId, payload);
      setBook(updated);
      populateFormFromBook(updated);
      setEditing(false);

      // Refresh author list in case a new author was created elsewhere
      booksApi.listAuthors().then((a) => setAuthorOptions(Array.isArray(a) ? a : [])).catch(() => {});
    } catch (e) {
      setErr(errorMessage(e));
    } finally {
      setSaving(false);
    }
  }

  // ── delete ──

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

  // ── inline sale ──

  const handleSaleRowChange = (index, field, value) => {
    setSaleRow((prev) => {
      if (typeof field === "object" && field !== null) return { ...prev, ...field };
      return { ...prev, [field]: value };
    });
  };

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

  // ── render guards ──

  if (loading) {
    return (
      <div className="p-6 text-slate-600">Loading…</div>
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

  // ── render ──

  return (
    <div className="min-h-screen flex items-start justify-center p-6">
      <div className="w-full max-w-6xl space-y-8">

        {/* ── Book Details Card ── */}
        <Card>
          <CardHeader
            title={editing ? "Edit Book" : "Book Details"}
            subtitle={
              editing
                ? "Update fields and save changes."
                : "View book metadata and cover art."
            }
          />
          <CardContent>
            {/* Action buttons */}
            <div className="flex items-center gap-2">
              {!editing ? (
                <>
                  <Button variant="secondary" onClick={() => setEditing(true)}>
                    Edit
                  </Button>
                  <Button variant="danger" onClick={() => { setErr(null); setDeleteOpen(true); }}>
                    Delete
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    variant="secondary"
                    onClick={() => {
                      populateFormFromBook(book);
                      setEditing(false);
                      setErr(null);
                    }}
                  >
                    Cancel
                  </Button>
                  <Button disabled={saving} onClick={onSave}>
                    {saving ? "Saving…" : "Save"}
                  </Button>
                </>
              )}
            </div>

            {err && <ErrorAlert className="mt-4">{err}</ErrorAlert>}

            {/* ── VIEW MODE ── */}
            {!editing ? (
              <div className="mt-6 flex flex-col gap-6 sm:flex-row">
                {/* Cover art */}
                <CoverImage path={book.cover_image_path} title={book.title} />

                {/* Metadata */}
                <div className="flex-1 space-y-4">
                  <DetailField label="Title">{book.title}</DetailField>

                  {/* Author — clickable link to author detail */}
                  <DetailField label="Author">
                    {book.author_id ? (
                      <button
                        type="button"
                        className="text-blue-600 underline hover:text-blue-800"
                        onClick={() => nav(`/authors/${book.author_id}`)}
                      >
                        {book.author_name || `Author #${book.author_id}`}
                      </button>
                    ) : (
                      "—"
                    )}
                  </DetailField>

                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <DetailField label="Publication">
                      {formatMonthYear(book.publication_date)}
                    </DetailField>
                    <DetailField label="Total Sales">
                      {book.total_sales_to_date ?? 0}
                    </DetailField>
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
                    <DetailField label="Cover Price">
                      {book.cover_price != null ? formatMoney(book.cover_price) : "—"}
                    </DetailField>
                    <DetailField label="Print Cost">
                      {book.print_cost != null ? formatMoney(book.print_cost) : "—"}
                    </DetailField>
                  </div>

                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <DetailField label="Distributor Royalty Rate">
                      {pct(book.distributor_author_royalty_rate)}
                    </DetailField>
                    <DetailField label="Hand-Sold Royalty Rate">
                      {pct(book.hand_sold_author_royalty_rate)}
                    </DetailField>
                  </div>

                  {book.series_name && (
                    <DetailField label="Series">
                      {book.series_display || `${book.series_name} (${book.series_position})`}
                    </DetailField>
                  )}

                  {book.cover_image_path && (
                    <DetailField label="Cover Image Path">
                      <span className="break-all font-mono text-xs text-slate-500">
                        {book.cover_image_path}
                      </span>
                    </DetailField>
                  )}
                </div>
              </div>
            ) : (
              /* ── EDIT MODE ── */
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
                    <div className="flex gap-2">
                      <Input
                        value={isbn10}
                        onChange={(e) => setIsbn10(e.target.value)}
                        placeholder="Leave blank to clear"
                      />
                      {isbn10 && (
                        <button
                          type="button"
                          className="flex-shrink-0 text-xs text-red-500 underline"
                          onClick={() => setIsbn10("")}
                        >
                          Clear
                        </button>
                      )}
                    </div>
                  </FormField>
                </div>

                {/* Author picker */}
                <FormField label="Author">
                  <div className="relative">
                    <Input
                      value={authorSearch}
                      onChange={(e) => {
                        setAuthorSearch(e.target.value);
                        setAuthorDropdownOpen(true);
                        if (!e.target.value) setSelectedAuthorId("");
                      }}
                      onFocus={() => setAuthorDropdownOpen(true)}
                      placeholder="Search authors…"
                    />
                    {authorDropdownOpen && filteredAuthors.length > 0 && (
                      <ul className="absolute z-20 mt-1 max-h-48 w-full overflow-auto rounded-md border border-slate-200 bg-white shadow-lg">
                        {filteredAuthors.map((a) => (
                          <li key={a.id}>
                            <button
                              type="button"
                              className="w-full px-3 py-2 text-left text-sm hover:bg-slate-100"
                              onMouseDown={() => selectAuthor(a)}
                            >
                              {a.name}
                            </button>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                  {selectedAuthorId && (
                    <p className="mt-1 text-xs text-slate-400">
                      Selected author ID: {selectedAuthorId}
                      {" · "}
                      <em>Changing the author only affects future sales.</em>
                    </p>
                  )}
                </FormField>

                {/* Royalty rates */}
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <FormField label="Distributor royalty rate (%)">
                    <Input
                      type="number"
                      min="0"
                      max="100"
                      step="1"
                      value={distributorRoyaltyRate}
                      onChange={(e) => setDistributorRoyaltyRate(e.target.value)}
                    />
                    <p className="mt-1 text-xs text-slate-400">
                      Percentage (0–100). Changes only affect future sales.
                    </p>
                  </FormField>
                  <FormField label="Hand-sold royalty rate (%)">
                    <Input
                      type="number"
                      min="0"
                      max="100"
                      step="1"
                      value={handSoldRoyaltyRate}
                      onChange={(e) => setHandSoldRoyaltyRate(e.target.value)}
                    />
                    <p className="mt-1 text-xs text-slate-400">
                      Percentage (0–100). Changes only affect future sales.
                    </p>
                  </FormField>
                </div>

                {/* Pricing */}
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <FormField label="Cover price ($)">
                    <Input
                      type="number"
                      min="0"
                      step="0.01"
                      value={coverPrice}
                      onChange={(e) => setCoverPrice(e.target.value)}
                    />
                  </FormField>
                  <FormField label="Print cost ($)">
                    <Input
                      type="number"
                      min="0"
                      step="0.01"
                      value={printCost}
                      onChange={(e) => setPrintCost(e.target.value)}
                    />
                  </FormField>
                </div>

                {/* Cover image */}
                <FormField label="Cover image path (optional)">
                  <div className="flex gap-2">
                    <Input
                      value={coverImagePath}
                      onChange={(e) => setCoverImagePath(e.target.value)}
                      placeholder="/static/covers/mybook.jpg — leave blank to clear"
                    />
                    {coverImagePath && (
                      <button
                        type="button"
                        className="flex-shrink-0 text-xs text-red-500 underline"
                        onClick={() => setCoverImagePath("")}
                      >
                        Clear
                      </button>
                    )}
                  </div>
                  {coverImagePath && (
                    <div className="mt-2">
                      <CoverImage path={coverImagePath} title={title} />
                    </div>
                  )}
                </FormField>

                {/* Series */}
                <SeriesFields
                  seriesName={seriesName}
                  setSeriesName={setSeriesName}
                  seriesPosition={seriesPosition}
                  setSeriesPosition={setSeriesPosition}
                />
              </div>
            )}
          </CardContent>
        </Card>

        {/* ── Delete dialog ── */}
        <DeleteBookDialog
          open={deleteOpen}
          book={book}
          deleting={deleting}
          onCancel={() => { if (!deleting) setDeleteOpen(false); }}
          onConfirm={onConfirmDelete}
        />

        {/* ── Sales Records Card ── */}
        <Card>
          <CardHeader title="Sales Records" subtitle="All sales records for this book." />
          <CardContent>
            <div className="mb-4 flex justify-end">
              {!showSaleEntry && (
                <Button onClick={() => setShowSaleEntry(true)}>Add Sale</Button>
              )}
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
                    {saleSubmitting ? "Submitting…" : "Submit Sale"}
                  </Button>
                </div>
              </div>
            )}

            {totalsErr && <ErrorAlert className="mb-4">{totalsErr}</ErrorAlert>}

            {/* Stat cards */}
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

            <BookSalesTable
              data={bookSales}
              loading={salesLoading}
              ordering={salesOrdering}
              onSort={handleSalesSort}
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
