// src/features/books/pages/CreateBookPage.jsx
import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Card,
  CardContent,
  CardHeader,
  Input,
  Button,
  MonthPicker,
  ErrorAlert,
  FormField,
} from "../../../shared/components";
import { AuthorsEditor } from "../components";
import { errorMessage } from "../../../shared/utils/errors";
import * as booksApi from "../api/booksApi";

function normalizeName(s) {
  return s.trim().replace(/\s+/g, " ");
}

export default function CreateBookPage() {
  const nav = useNavigate();

  // Book fields
  const [title, setTitle] = useState("");
  const [publicationMonth, setPublicationMonth] = useState("2000-01");
  const [isbn13, setIsbn13] = useState("");
  const [isbn10, setIsbn10] = useState("");

  // Author options
  const [authorOptions, setAuthorOptions] = useState([]);
  const [authorsLoading, setAuthorsLoading] = useState(true);
  const [authorsErr, setAuthorsErr] = useState(null);

  // Author rows
  const [authors, setAuthors] = useState([{ author_name: "", royalty_rate: "0.50" }]);
  const [openAuthorIdx, setOpenAuthorIdx] = useState(null);

  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState(null);

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

  async function onSubmit(e) {
    e.preventDefault();
    setErr(null);
    setSubmitting(true);

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
              <FormField label="Title">
                <Input value={title} onChange={(e) => setTitle(e.target.value)} required />
              </FormField>

              <MonthPicker
                label="Publication date (month, year)"
                value={publicationMonth}
                onChange={setPublicationMonth}
                required
              />

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <FormField label="ISBN-13">
                  <Input
                    value={isbn13}
                    onChange={(e) => setIsbn13(e.target.value)}
                    placeholder="978..."
                    required
                  />
                </FormField>

                <FormField label="ISBN-10 (optional)">
                  <Input
                    value={isbn10}
                    onChange={(e) => setIsbn10(e.target.value)}
                    placeholder="0441172717"
                  />
                </FormField>
              </div>

              {authorsErr && (
                <ErrorAlert>Failed to load authors: {authorsErr}</ErrorAlert>
              )}

              <AuthorsEditor
                authors={authors}
                setAuthors={setAuthors}
                authorOptions={authorOptions}
                authorsLoading={authorsLoading}
                openAuthorIdx={openAuthorIdx}
                setOpenAuthorIdx={setOpenAuthorIdx}
              />

              <div className="text-xs text-slate-500">
                Royalty rate is a decimal (e.g., 0.50 for 50%).
              </div>

              <div className="flex items-center justify-end gap-2">
                <Button type="button" variant="secondary" onClick={() => nav("/books")}>
                  Cancel
                </Button>
                <Button disabled={submitting} className="min-w-[120px]">
                  {submitting ? "Creating..." : "Create"}
                </Button>
              </div>

              {err && <ErrorAlert>{err}</ErrorAlert>}
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
