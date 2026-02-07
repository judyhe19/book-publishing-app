// src/features/books/pages/CreateBookPage.jsx
import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader } from "../../../shared/components/Card";
import { Input } from "../../../shared/components/Input";
import { Button } from "../../../shared/components/Button";
import { errorMessage } from "../../../shared/utils/errors";
import * as booksApi from "../api/booksApi";

function normalizeName(s) {
  return s.trim().replace(/\s+/g, " ");
}

export default function CreateBookPage() {
  const nav = useNavigate();

  // --- Book fields ---
  const [title, setTitle] = useState("");
  const [publicationMonth, setPublicationMonth] = useState("2000-01"); // YYYY-MM
  const [isbn13, setIsbn13] = useState("");
  const [isbn10, setIsbn10] = useState("");

  // --- Author options ---
  // shape: [{id, name}]
  const [authorOptions, setAuthorOptions] = useState([]);
  const [authorsLoading, setAuthorsLoading] = useState(true);
  const [authorsErr, setAuthorsErr] = useState(null);

  // --- Author rows (name + royalty) ---
  const [authors, setAuthors] = useState([{ author_name: "", royalty_rate: "0.50" }]);

  // Which author input dropdown is open (null = none)
  const [openAuthorIdx, setOpenAuthorIdx] = useState(null);

  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState(null);

  // Prevent duplicates across rows
  const selectedNames = useMemo(() => {
    return new Set(
      authors
        .map((a) => normalizeName(a.author_name).toLowerCase())
        .filter((x) => x.length > 0)
    );
  }, [authors]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setAuthorsLoading(true);
      setAuthorsErr(null);
      try {
        const data = await booksApi.listAuthors();
        if (!cancelled) setAuthorOptions(Array.isArray(data) ? data : []);
      } catch (e) {
        if (!cancelled) setAuthorsErr(errorMessage(e));
      } finally {
        if (!cancelled) setAuthorsLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  function updateAuthorRow(idx, patch) {
    setAuthors((prev) => prev.map((row, i) => (i === idx ? { ...row, ...patch } : row)));
  }

  function addAuthorRow() {
    setAuthors((prev) => [...prev, { author_name: "", royalty_rate: "0.50" }]);
    // Prevent the “auto-open on add” bug
    setOpenAuthorIdx(null);
  }

  function removeAuthorRow(idx) {
    setAuthors((prev) => prev.filter((_, i) => i !== idx));
    // Avoid index-shift issues
    setOpenAuthorIdx(null);
  }

  async function onSubmit(e) {
    e.preventDefault();
    setErr(null);
    setSubmitting(true);

    try {
      const cleanedAuthors = authors.map((r) => ({
        author_name: normalizeName(r.author_name),
        royalty_rate: String(r.royalty_rate).trim(),
      }));

      if (!title.trim()) throw new Error("Title is required.");
      if (!publicationMonth) throw new Error("Publication date (month, year) is required.");

      for (const r of cleanedAuthors) {
        if (!r.author_name) throw new Error("Each author must have a name.");
        if (!r.royalty_rate) throw new Error("Each author must have a royalty rate.");
      }

      // duplicates by name
      const nameSet = new Set(cleanedAuthors.map((r) => r.author_name.toLowerCase()));
      if (nameSet.size !== cleanedAuthors.length) {
        throw new Error("Please don’t enter the same author more than once.");
      }

      // map existing authors by name
      const byName = new Map(authorOptions.map((a) => [normalizeName(a.name).toLowerCase(), a]));

      // resolve IDs (create missing authors via POST /authors/)
      const resolvedAuthors = [];
      for (const r of cleanedAuthors) {
        const key = r.author_name.toLowerCase();
        let found = byName.get(key);

        if (!found) {
          found = await booksApi.createAuthor(r.author_name); // returns {id, name} (200 or 201)
          byName.set(key, found);

          // update options in UI
          setAuthorOptions((prev) => {
            const exists = prev.some((a) => a.id === found.id);
            const next = exists ? prev : [...prev, found];
            return next.sort((a, b) => a.name.localeCompare(b.name));
          });
        }

        resolvedAuthors.push({
          author_id: found.id,
          royalty_rate: r.royalty_rate,
        });
      }

      const payload = {
        title: title.trim(),
        publication_date: `${publicationMonth}-01`, // default day = 1
        isbn_13: isbn13.replaceAll("-", "").trim(),
        isbn_10: isbn10.trim() === "" ? null : isbn10.replaceAll("-", "").trim(),
        authors: resolvedAuthors,
      };

      await booksApi.createBook(payload);
      nav("/books", { replace: true });
    } catch (e2) {
      setErr(errorMessage(e2));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-start justify-center p-6">
      <div className="w-full max-w-3xl">
        <Card>
          <CardHeader title="Create Book" subtitle="Add a new book to the catalog." />
          <CardContent>
            <form className="space-y-5" onSubmit={onSubmit}>
              {/* Title */}
              <div>
                <label className="text-sm font-medium text-slate-700">Title</label>
                <div className="mt-1">
                  <Input value={title} onChange={(e) => setTitle(e.target.value)} required />
                </div>
              </div>

              {/* Month/Year picker */}
              <div>
                <label className="text-sm font-medium text-slate-700">
                  Publication date (month, year)
                </label>
                <div className="mt-1">
                  <input
                    type="month"
                    className="w-full rounded-xl border border-slate-200 px-3 py-2"
                    value={publicationMonth}
                    onChange={(e) => setPublicationMonth(e.target.value)}
                    required
                  />
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  Day will default to the 1st in the database.
                </div>
              </div>

              {/* ISBNs */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="text-sm font-medium text-slate-700">ISBN-13</label>
                  <div className="mt-1">
                    <Input
                      value={isbn13}
                      onChange={(e) => setIsbn13(e.target.value)}
                      placeholder="978..."
                      maxLength={13}
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium text-slate-700">ISBN-10 (optional)</label>
                  <div className="mt-1">
                    <Input
                      value={isbn10}
                      onChange={(e) => setIsbn10(e.target.value)}
                      placeholder="0441172717"
                      maxLength={10}
                    />
                  </div>
                </div>
              </div>

              {/* Authors */}
              <div>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-sm font-medium text-slate-700">Authors</div>
                    <div className="text-xs text-slate-500">
                      Type the author name(s). New names will be created when you save.
                    </div>
                  </div>
                  <Button type="button" variant="secondary" onClick={addAuthorRow}>
                    Add author
                  </Button>
                </div>

                {authorsErr && (
                  <div className="mt-2 text-sm text-red-600">
                    Failed to load authors: {authorsErr}
                  </div>
                )}

                <div className="mt-3 space-y-2">
                  {authors.map((row, idx) => {
                    const typed = normalizeName(row.author_name);
                    const typedKey = typed.toLowerCase();

                    const matches = authorsLoading
                      ? []
                      : authorOptions
                          .filter((a) => {
                            const key = normalizeName(a.name).toLowerCase();
                            const selectedElsewhere = selectedNames.has(key) && key !== typedKey;
                            return !selectedElsewhere && (typedKey === "" || key.includes(typedKey));
                          })
                          .slice(0, 20);

                    const showDropdown =
                      openAuthorIdx === idx && !authorsLoading && matches.length > 0;

                    return (
                      <div key={idx} className="flex flex-col gap-2 sm:flex-row sm:items-center">
                        {/* Author input + dropdown */}
                        <div className="sm:w-[28rem] w-full relative">
                          <input
                            className="w-full rounded-xl border border-slate-200 px-3 py-2"
                            value={row.author_name}
                            onChange={(e) => {
                              updateAuthorRow(idx, { author_name: e.target.value });
                              // Open only for the row the user is interacting with
                              setOpenAuthorIdx(idx);
                            }}
                            onFocus={() => {
                              // Open on focus (won't happen automatically on add unless something focuses it)
                              setOpenAuthorIdx(idx);
                            }}
                            onBlur={() => {
                              // Delay so option click can register before closing
                              setTimeout(() => setOpenAuthorIdx(null), 120);
                            }}
                            placeholder={authorsLoading ? "Loading authors..." : "Enter an author name..."}
                            required
                          />

                          {showDropdown ? (
                            <div className="absolute z-20 mt-1 w-full rounded-xl border border-slate-200 bg-white shadow-lg overflow-hidden">
                              {matches.map((a) => (
                                <button
                                  key={a.id}
                                  type="button"
                                  className="block w-full text-left px-3 py-2 hover:bg-slate-50"
                                  onMouseDown={(ev) => {
                                    // Prevent blur firing before we set value
                                    ev.preventDefault();
                                  }}
                                  onClick={() => {
                                    updateAuthorRow(idx, { author_name: a.name });
                                    setOpenAuthorIdx(null);
                                  }}
                                >
                                  {a.name}
                                </button>
                              ))}
                            </div>
                          ) : null}
                        </div>

                        {/* Royalty rate */}
                        <div className="sm:w-40 w-full">
                          <input
                            className="w-full rounded-xl border border-slate-200 px-3 py-2"
                            value={row.royalty_rate}
                            onChange={(e) => updateAuthorRow(idx, { royalty_rate: e.target.value })}
                            placeholder="0.50"
                            required
                          />
                        </div>

                        {/* Remove row */}
                        {authors.length > 1 ? (
                          <Button type="button" variant="secondary" onClick={() => removeAuthorRow(idx)}>
                            Remove
                          </Button>
                        ) : null}
                      </div>
                    );
                  })}
                </div>

                <div className="mt-2 text-xs text-slate-500">
                  Royalty rate is a decimal (e.g., 0.50 for 50%).
                </div>
              </div>

              {/* Button actions */}
              <div className="flex items-center justify-end gap-2">
                <Button type="button" variant="secondary" onClick={() => nav("/books")}>
                  Cancel
                </Button>
                <Button disabled={submitting} className="min-w-[120px]">
                  {submitting ? "Creating..." : "Create"}
                </Button>
              </div>

              {err && (
                <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 whitespace-pre-wrap">
                  {err}
                </div>
              )}
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
