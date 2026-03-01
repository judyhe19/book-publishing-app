// src/features/books/components/AddBookToSeriesModal.jsx
import React, { useEffect, useState } from "react";
import { Button, ErrorAlert, Input } from "../../../shared/components";
import { errorMessage } from "../../../shared/utils/errors";
import * as booksApi from "../api/booksApi";

/**
 * Modal for searching and adding a book to the current series at a given position.
 *
 * Props:
 *   open                boolean
 *   onClose             fn
 *   onAdd               fn(book, position)  — called with the selected book and 1-indexed position
 *   currentSeriesBookIds  number[]          — IDs already in the series (excluded from results)
 *   currentSeriesCount    number            — current number of books in the series
 */
export default function AddBookToSeriesModal({
  open,
  onClose,
  onAdd,
  currentSeriesBookIds,
  currentSeriesCount,
}) {
  const [allBooks, setAllBooks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  const [search, setSearch] = useState("");
  const [selectedBook, setSelectedBook] = useState(null);
  const [position, setPosition] = useState("");

  const maxPos = currentSeriesCount + 1;

  // Fetch all books (excluding current series members) when modal opens
  useEffect(() => {
    if (!open) return;

    setSearch("");
    setSelectedBook(null);
    setPosition(String(maxPos));
    setErr(null);

    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const data = await booksApi.getBooks("page_size=500&ordering=title");
        const results = data.results || data;
        if (!cancelled) {
          const idSet = new Set(currentSeriesBookIds);
          setAllBooks(
            Array.isArray(results)
              ? results.filter((b) => !idSet.has(b.id) && !b.series_name)
              : []
          );
        }
      } catch (e) {
        if (!cancelled) setErr(errorMessage(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [open]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!open) return null;

  const filtered = allBooks.filter((b) =>
    (b.title || "").toLowerCase().includes(search.toLowerCase())
  );

  function handleAdd() {
    if (!selectedBook) return;
    const pos = Math.max(1, Math.min(parseInt(position, 10) || maxPos, maxPos));
    onAdd(selectedBook, pos);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <button
        type="button"
        className="absolute inset-0 bg-black/40"
        onClick={onClose}
        aria-label="Close dialog"
      />

      {/* Dialog */}
      <div className="relative w-full max-w-lg rounded-2xl bg-white shadow-xl border border-slate-200 flex flex-col max-h-[80vh]">
        {/* Header */}
        <div className="p-5 border-b border-slate-100">
          <div className="text-lg font-semibold text-slate-900">Add Book to Series</div>
        </div>

        {/* Body */}
        <div className="p-5 flex-1 overflow-hidden flex flex-col gap-4 min-h-0">
          {err && <ErrorAlert>{err}</ErrorAlert>}

          {/* Search */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Search books
            </label>
            <Input
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setSelectedBook(null);
              }}
              placeholder="Type to filter by title…"
              autoFocus
            />
          </div>

          {/* Book list */}
          <div className="flex-1 overflow-auto border border-slate-200 rounded-lg min-h-0">
            {loading ? (
              <p className="p-3 text-sm text-slate-500">Loading books…</p>
            ) : filtered.length === 0 ? (
              <p className="p-3 text-sm text-slate-500">No books found.</p>
            ) : (
              <ul>
                {filtered.map((b) => (
                  <li key={b.id}>
                    <button
                      type="button"
                      className={[
                        "w-full text-left px-3 py-2 text-sm flex flex-col border-b border-slate-100 last:border-0",
                        selectedBook?.id === b.id
                          ? "bg-slate-900 text-white"
                          : "hover:bg-slate-50 text-slate-900",
                      ].join(" ")}
                      onClick={() => setSelectedBook(b)}
                    >
                      <span className="font-medium">{b.title}</span>
                      {b.series_name && (
                        <span
                          className={[
                            "text-xs",
                            selectedBook?.id === b.id
                              ? "text-slate-300"
                              : "text-slate-400",
                          ].join(" ")}
                        >
                          Currently in: {b.series_name}
                        </span>
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Position */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Insert at position
            </label>
            <Input
              type="number"
              min="1"
              max={maxPos}
              value={position}
              onChange={(e) => setPosition(e.target.value)}
            />
            <p className="mt-1 text-xs text-slate-400">
              Valid range: 1–{maxPos}. Other books shift to make room.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="p-5 pt-0 flex items-center justify-end gap-2 border-t border-slate-100">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleAdd} disabled={!selectedBook}>
            Add to Series
          </Button>
        </div>
      </div>
    </div>
  );
}
