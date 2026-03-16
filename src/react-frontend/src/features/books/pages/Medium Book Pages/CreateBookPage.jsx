// src/features/books/pages/CreateBookPage.jsx
import React, { useEffect, useState } from "react";
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

function cleanIsbn(s) {
  return (s || "").replaceAll("-", "").trim();
}

export default function CreateBookPage() {
  const nav = useNavigate();

  // Book fields
  const [title, setTitle] = useState("");
  const [publicationMonth, setPublicationMonth] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
  });
  const [isbn13, setIsbn13] = useState("");
  const [isbn10, setIsbn10] = useState("");

  // NEW required fields
  const [coverPrice, setCoverPrice] = useState(""); // required, non-negative
  const [printCost, setPrintCost] = useState(""); // required, non-negative

  // NEW optional series/cover
  const [seriesName, setSeriesName] = useState("");
  const [seriesPosition, setSeriesPosition] = useState(""); // optional but required if seriesName present
  const [coverImagePath, setCoverImagePath] = useState(""); // optional string path (served from /static)

  // Author options (existing authors only)
  const [authorOptions, setAuthorOptions] = useState([]);
  const [authorsLoading, setAuthorsLoading] = useState(true);
  const [authorsErr, setAuthorsErr] = useState(null);

  // Evolution 2: keep AuthorsEditor API but use single row:
  // { author_id, author_name, distributor_author_royalty_rate, hand_sold_author_royalty_rate }
  const [authors, setAuthors] = useState([
    {
      author_id: null,
      author_name: "",
      distributor_author_royalty_rate: "0.50",
      hand_sold_author_royalty_rate: "0.20",
    },
  ]);
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
      const a0 = authors?.[0] || {};

      const payload = {
        title: title.trim(),
        publication_date: publicationMonth,
        isbn_13: cleanIsbn(isbn13),
        isbn_10: cleanIsbn(isbn10) === "" ? null : cleanIsbn(isbn10),

        // Single-author book
        author_id: a0.author_id,

        // Book-level royalty rates
        distributor_author_royalty_rate: String(a0.distributor_author_royalty_rate ?? "0.50").trim(),
        hand_sold_author_royalty_rate: String(a0.hand_sold_author_royalty_rate ?? "0.20").trim(),

        // Required monetary fields
        cover_price: String(coverPrice).trim(),
        print_cost: String(printCost).trim(),

        // Optional fields
        series_name: seriesName.trim() === "" ? null : seriesName.trim(),
        series_position:
          seriesName.trim() === ""
            ? null
            : seriesPosition === ""
            ? null
            : Number(seriesPosition),
        cover_image_path: coverImagePath.trim() === "" ? null : coverImagePath.trim(),
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

              {/* NEW: required money fields */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <FormField label="Cover price">
                  <Input
                    value={coverPrice}
                    onChange={(e) => setCoverPrice(e.target.value)}
                    placeholder="19.99"
                    required
                  />
                </FormField>

                <FormField label="Print cost">
                  <Input
                    value={printCost}
                    onChange={(e) => setPrintCost(e.target.value)}
                    placeholder="4.25"
                    required
                  />
                </FormField>
              </div>

              {/* NEW: optional series */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <FormField label="Series (optional)">
                  <Input
                    value={seriesName}
                    onChange={(e) => setSeriesName(e.target.value)}
                    placeholder='e.g., "Lord of the Rings"'
                  />
                </FormField>

                <FormField label="Series position (required if series set)">
                  <Input
                    value={seriesPosition}
                    onChange={(e) => setSeriesPosition(e.target.value)}
                    placeholder="e.g., 3"
                    disabled={seriesName.trim() === ""}
                  />
                </FormField>
              </div>

              {/* NEW: optional cover image */}
              <FormField label="Cover image path (optional)">
                <Input
                  value={coverImagePath}
                  onChange={(e) => setCoverImagePath(e.target.value)}
                  placeholder='/static/covers/my-book.jpg'
                />
                {coverImagePath.trim() ? (
                  <div className="mt-2">
                    <div className="text-xs text-slate-500 mb-1">Preview</div>
                    <img
                      src={coverImagePath.trim()}
                      alt="Cover preview"
                      className="max-h-56 w-auto rounded-xl border border-slate-200 shadow-sm"
                    />
                  </div>
                ) : null}
              </FormField>

              {authorsErr && <ErrorAlert>Failed to load authors: {authorsErr}</ErrorAlert>}

              <AuthorsEditor
                authors={authors}
                setAuthors={setAuthors}
                authorOptions={authorOptions}
                authorsLoading={authorsLoading}
                openAuthorIdx={openAuthorIdx}
                setOpenAuthorIdx={setOpenAuthorIdx}
              />

              <div className="text-xs text-slate-500">
                Royalty rates are decimals (e.g., 0.50 for 50%).
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