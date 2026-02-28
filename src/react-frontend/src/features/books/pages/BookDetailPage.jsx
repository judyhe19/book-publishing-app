// src/features/books/pages/BookDetailPage.jsx
import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Card,
  CardContent,
  CardHeader,
  Button,
  ErrorAlert,
} from "../../../shared/components";
import {
  BookViewMode,
  BookEditMode,
  BookSalesSection,
  DeleteBookDialog,
} from "../components";
import { errorMessage } from "../../../shared/utils/errors";
import * as booksApi from "../api/booksApi";

/**
 * Book detail page with view/edit modes and sales section.
 * Refactored to use extracted components for clarity.
 */
export default function BookDetailPage() {
  const { bookId } = useParams();
  const nav = useNavigate();

  // Fetch state
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [book, setBook] = useState(null);

  // UI state
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Form state
  const [title, setTitle] = useState("");
  const [publicationMonth, setPublicationMonth] = useState("");
  const [isbn13, setIsbn13] = useState("");
  const [isbn10, setIsbn10] = useState("");
  const [authorOptions, setAuthorOptions] = useState([]);
  const [selectedAuthorId, setSelectedAuthorId] = useState("");
  const [authorSearch, setAuthorSearch] = useState("");
  const [distributorRoyaltyRate, setDistributorRoyaltyRate] = useState("0.50");
  const [handSoldRoyaltyRate, setHandSoldRoyaltyRate] = useState("0.20");
  const [coverPrice, setCoverPrice] = useState("");
  const [printCost, setPrintCost] = useState("");
  const [coverImagePath, setCoverImagePath] = useState("");
  const [coverImageFile, setCoverImageFile] = useState(null);
  const [seriesName, setSeriesName] = useState("");
  const [seriesPosition, setSeriesPosition] = useState("");
  const [seriesOptions, setSeriesOptions] = useState([]);

  // Populate form from book data
  function populateFormFromBook(b) {
    if (!b) return;
    setTitle(b.title || "");
    setPublicationMonth(b.publication_date || "");
    setIsbn13(b.isbn_13 || "");
    setIsbn10(b.isbn_10 || "");
    setSelectedAuthorId(b.author_id != null ? String(b.author_id) : "");
    setAuthorSearch(b.author_name || "");
    setDistributorRoyaltyRate(String(b.distributor_author_royalty_rate ?? "0.50"));
    setHandSoldRoyaltyRate(String(b.hand_sold_author_royalty_rate ?? "0.20"));
    setCoverPrice(b.cover_price != null ? String(b.cover_price) : "");
    setPrintCost(b.print_cost != null ? String(b.print_cost) : "");
    setCoverImagePath(b.cover_image_path || "");
    setCoverImageFile(null);
    setSeriesName(b.series_name || "");
    setSeriesPosition(b.series_position != null ? String(b.series_position) : "");
  }

  // Load book and authors
  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setErr(null);

      try {
        const [b, a, s] = await Promise.all([
          booksApi.getBook(bookId),
          booksApi.listAuthors().catch(() => []),
          booksApi.listSeries().catch(() => []),
        ]);

        if (cancelled) return;

        setBook(b);
        populateFormFromBook(b);
        setAuthorOptions(Array.isArray(a) ? a : []);
        setSeriesOptions(Array.isArray(s) ? s : []);
      } catch (e) {
        if (!cancelled) setErr(errorMessage(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [bookId]);

  // Refresh book data
  async function refreshBook() {
    try {
      const b = await booksApi.getBook(bookId);
      setBook(b);
    } catch (e) {
      console.error("Error refreshing book:", e);
    }
  }

  // Save changes
  async function onSave() {
    setErr(null);
    setSaving(true);

    try {
      // Upload cover image first if a new file was selected
      let finalCoverImagePath = coverImagePath.trim() === "" ? null : coverImagePath.trim();

      if (coverImageFile) {
        const uploadResult = await booksApi.uploadCoverImage(coverImageFile);
        finalCoverImagePath = uploadResult.cover_image_path;
      }

      const payload = {
        title: title.trim(),
        publication_date: publicationMonth,
        isbn_13: isbn13.replaceAll("-", "").trim(),
        isbn_10: isbn10.trim() === "" ? null : isbn10.replaceAll("-", "").trim(),
        author_id: selectedAuthorId ? Number(selectedAuthorId) : undefined,
        distributor_author_royalty_rate: distributorRoyaltyRate,
        hand_sold_author_royalty_rate: handSoldRoyaltyRate,
        cover_price: coverPrice,
        print_cost: printCost,
        cover_image_path: finalCoverImagePath,
        series_name: seriesName.trim() === "" ? null : seriesName.trim(),
        series_position: seriesPosition === "" || seriesPosition == null ? null : Number(seriesPosition),
      };

      const updated = await booksApi.updateBook(bookId, payload);
      setBook(updated);
      populateFormFromBook(updated);
      setEditing(false);

      // Refresh author and series lists
      booksApi.listAuthors().then((a) => setAuthorOptions(Array.isArray(a) ? a : [])).catch(() => {});
      booksApi.listSeries().then((s) => setSeriesOptions(Array.isArray(s) ? s : [])).catch(() => {});
    } catch (e) {
      setErr(errorMessage(e));
    } finally {
      setSaving(false);
    }
  }

  // Delete book
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

  // Loading state
  if (loading) {
    return <div className="p-6 text-slate-600">Loading…</div>;
  }

  // Not found state
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
      <div className="w-full max-w-6xl space-y-8">

        {/* Book Details Card */}
        <Card>
          <CardHeader
            title={editing ? "Edit Book" : "Book Details"}
            subtitle={editing ? "Update fields and save changes." : "View book metadata and cover art."}
          />
          <CardContent>
            {/* Action buttons */}
            <div className="flex items-center justify-between gap-2">
              <Button variant="secondary" onClick={() => nav("/books")}>
                All Books
              </Button>
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
            </div>

            {err && <ErrorAlert className="mt-4">{err}</ErrorAlert>}

            {/* View or Edit mode */}
            {!editing ? (
              <BookViewMode book={book} />
            ) : (
              <BookEditMode
                title={title}
                setTitle={setTitle}
                publicationMonth={publicationMonth}
                setPublicationMonth={setPublicationMonth}
                isbn13={isbn13}
                setIsbn13={setIsbn13}
                isbn10={isbn10}
                setIsbn10={setIsbn10}
                authorOptions={authorOptions}
                selectedAuthorId={selectedAuthorId}
                setSelectedAuthorId={setSelectedAuthorId}
                authorSearch={authorSearch}
                setAuthorSearch={setAuthorSearch}
                distributorRoyaltyRate={distributorRoyaltyRate}
                setDistributorRoyaltyRate={setDistributorRoyaltyRate}
                handSoldRoyaltyRate={handSoldRoyaltyRate}
                setHandSoldRoyaltyRate={setHandSoldRoyaltyRate}
                coverPrice={coverPrice}
                setCoverPrice={setCoverPrice}
                printCost={printCost}
                setPrintCost={setPrintCost}
                coverImagePath={coverImagePath}
                setCoverImagePath={setCoverImagePath}
                onCoverImageFileChange={setCoverImageFile}
                seriesName={seriesName}
                setSeriesName={setSeriesName}
                seriesPosition={seriesPosition}
                setSeriesPosition={setSeriesPosition}
                seriesOptions={seriesOptions}
                originalSeriesName={book.series_name}
              />
            )}
          </CardContent>
        </Card>

        {/* Delete dialog */}
        <DeleteBookDialog
          open={deleteOpen}
          book={book}
          deleting={deleting}
          onCancel={() => { if (!deleting) setDeleteOpen(false); }}
          onConfirm={onConfirmDelete}
        />

        {/* Sales section */}
        <BookSalesSection
          bookId={bookId}
          book={book}
          onSaleCreated={refreshBook}
        />

      </div>
    </div>
  );
}