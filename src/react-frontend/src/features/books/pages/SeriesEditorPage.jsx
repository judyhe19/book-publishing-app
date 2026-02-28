// src/features/books/pages/SeriesEditorPage.jsx
import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  ErrorAlert,
} from "../../../shared/components";
import { errorMessage } from "../../../shared/utils/errors";
import * as booksApi from "../api/booksApi";

export default function SeriesEditorPage() {
  const nav = useNavigate();

  const [seriesOptions, setSeriesOptions] = useState([]);
  const [seriesLoading, setSeriesLoading] = useState(true);

  const [selectedSeries, setSelectedSeries] = useState("");
  const [books, setBooks] = useState([]); // [{id, title, series_position}]
  const [booksLoading, setBooksLoading] = useState(false);
  const [dirty, setDirty] = useState(false);

  const [saving, setSaving] = useState(false);
  const [saveErr, setSaveErr] = useState(null);
  const [saveOk, setSaveOk] = useState(false);

  // Drag state
  const dragIndex = useRef(null);
  const [dragOver, setDragOver] = useState(null);

  // Load series list on mount
  useEffect(() => {
    let cancelled = false;
    async function load() {
      setSeriesLoading(true);
      try {
        const data = await booksApi.listSeries();
        if (!cancelled) setSeriesOptions(Array.isArray(data) ? data : []);
      } catch {
        // non-fatal
      } finally {
        if (!cancelled) setSeriesLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  // Load books when series changes
  useEffect(() => {
    if (!selectedSeries) {
      setBooks([]);
      setDirty(false);
      return;
    }
    let cancelled = false;
    async function load() {
      setBooksLoading(true);
      setSaveErr(null);
      setSaveOk(false);
      try {
        const encoded = encodeURIComponent(selectedSeries);
        const data = await booksApi.getBooks(
          `series_name=${encoded}&ordering=series_position&page_size=200`
        );
        const results = data.results || data;
        if (!cancelled) {
          setBooks(Array.isArray(results) ? results : []);
          setDirty(false);
        }
      } catch (e) {
        if (!cancelled) setSaveErr(errorMessage(e));
      } finally {
        if (!cancelled) setBooksLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [selectedSeries]);

  // --- Drag and drop handlers ---

  function onDragStart(e, idx) {
    dragIndex.current = idx;
    e.dataTransfer.effectAllowed = "move";
  }

  function onDragOver(e, idx) {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setDragOver(idx);
  }

  function onDrop(e, idx) {
    e.preventDefault();
    const from = dragIndex.current;
    if (from === null || from === idx) {
      setDragOver(null);
      return;
    }
    const updated = [...books];
    const [moved] = updated.splice(from, 1);
    updated.splice(idx, 0, moved);
    setBooks(updated);
    setDirty(true);
    setDragOver(null);
    dragIndex.current = null;
  }

  function onDragEnd() {
    setDragOver(null);
    dragIndex.current = null;
  }

  // --- Remove a book from the series (locally only) ---

  function removeBook(bookId) {
    setBooks((prev) => prev.filter((b) => b.id !== bookId));
    setDirty(true);
  }

  // --- Save ---

  async function onSave() {
    if (!selectedSeries) return;
    setSaving(true);
    setSaveErr(null);
    setSaveOk(false);
    try {
      const bookIds = books.map((b) => b.id);
      await booksApi.reorderSeries(selectedSeries, bookIds);

      // Refresh series list (in case series was emptied and no longer exists)
      const updatedSeries = await booksApi.listSeries();
      const seriesList = Array.isArray(updatedSeries) ? updatedSeries : [];
      setSeriesOptions(seriesList);

      // If the series still exists reload it; otherwise clear selection
      const stillExists = seriesList.some((s) => s.name === selectedSeries);
      if (stillExists) {
        // Re-load books to get fresh positions
        const encoded = encodeURIComponent(selectedSeries);
        const data = await booksApi.getBooks(
          `series_name=${encoded}&ordering=series_position&page_size=200`
        );
        const results = data.results || data;
        setBooks(Array.isArray(results) ? results : []);
      } else {
        setSelectedSeries("");
        setBooks([]);
      }
      setDirty(false);
      setSaveOk(true);
    } catch (e) {
      setSaveErr(errorMessage(e));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="min-h-screen flex items-start justify-center p-6">
      <div className="w-full max-w-3xl">
        <Card>
          <CardHeader
            title="Series Editor"
            subtitle="Select a series to reorder or remove books."
          />
          <CardContent>
            <div className="flex items-center justify-between gap-2 mb-6">
              <Button variant="secondary" onClick={() => nav("/books")}>
                All Books
              </Button>
            </div>

            {/* Series selector */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Select series
              </label>
              {seriesLoading ? (
                <p className="text-sm text-slate-500">Loading series…</p>
              ) : seriesOptions.length === 0 ? (
                <p className="text-sm text-slate-500">
                  No series found. Assign books to a series to get started.
                </p>
              ) : (
                <select
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={selectedSeries}
                  onChange={(e) => {
                    setSelectedSeries(e.target.value);
                    setSaveOk(false);
                  }}
                >
                  <option value="">— Select a series —</option>
                  {seriesOptions.map((s) => (
                    <option key={s.name} value={s.name}>
                      {s.name} ({s.count} {s.count === 1 ? "book" : "books"})
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Books table */}
            {selectedSeries && (
              <>
                {booksLoading ? (
                  <p className="text-sm text-slate-500">Loading books…</p>
                ) : books.length === 0 ? (
                  <p className="text-sm text-slate-500">No books in this series.</p>
                ) : (
                  <>
                    <p className="text-xs text-slate-500 mb-3">
                      Drag rows to reorder. Changes are not saved until you click Save.
                    </p>
                    <table className="w-full text-sm border-collapse">
                      <thead>
                        <tr className="border-b border-slate-200 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">
                          <th className="py-2 pr-2 w-8"></th>
                          <th className="py-2 pr-4 w-12">#</th>
                          <th className="py-2">Title</th>
                          <th className="py-2 w-20"></th>
                        </tr>
                      </thead>
                      <tbody>
                        {books.map((book, idx) => (
                          <tr
                            key={book.id}
                            draggable
                            onDragStart={(e) => onDragStart(e, idx)}
                            onDragOver={(e) => onDragOver(e, idx)}
                            onDrop={(e) => onDrop(e, idx)}
                            onDragEnd={onDragEnd}
                            className={[
                              "border-b border-slate-100 transition-colors",
                              dragOver === idx
                                ? "bg-blue-50 border-t-2 border-t-blue-400"
                                : "hover:bg-slate-50",
                            ].join(" ")}
                          >
                            {/* Drag handle */}
                            <td className="py-2 pr-2 text-slate-400 cursor-grab select-none text-lg leading-none">
                              ⠿
                            </td>
                            {/* Position (1-indexed display) */}
                            <td className="py-2 pr-4 text-slate-500 font-mono">
                              {idx + 1}
                            </td>
                            {/* Title */}
                            <td className="py-2 text-slate-900">{book.title}</td>
                            {/* Remove */}
                            <td className="py-2 text-right">
                              <button
                                type="button"
                                className="text-xs text-red-500 hover:text-red-700 underline"
                                onClick={() => removeBook(book.id)}
                              >
                                Remove
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </>
                )}

                {/* Error / success feedback */}
                {saveErr && (
                  <ErrorAlert className="mt-4">{saveErr}</ErrorAlert>
                )}
                {saveOk && (
                  <p className="mt-4 text-sm text-green-600 font-medium">
                    Series saved successfully.
                  </p>
                )}

                {/* Save button */}
                <div className="mt-6 flex justify-end">
                  <Button
                    onClick={onSave}
                    disabled={saving || !dirty}
                  >
                    {saving ? "Saving…" : "Save"}
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
