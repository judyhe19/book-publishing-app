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
import { AuthorPicker, CoverImageField, SeriesPicker } from "../components";
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

  // Pricing fields
  const [coverPrice, setCoverPrice] = useState("");
  const [printCost, setPrintCost] = useState("");

  // Series fields
  const [seriesName, setSeriesName] = useState("");
  const [seriesPosition, setSeriesPosition] = useState("");

  // Cover image
  const [coverImagePath, setCoverImagePath] = useState("");
  const [coverImageFile, setCoverImageFile] = useState(null);

  // Amazon ASIN
  const [amazonAsin, setAmazonAsin] = useState("");

  // Author (single author model)
  const [authorOptions, setAuthorOptions] = useState([]);
  const [authorsLoading, setAuthorsLoading] = useState(true);
  const [authorsErr, setAuthorsErr] = useState(null);
  const [selectedAuthorId, setSelectedAuthorId] = useState("");
  const [authorSearch, setAuthorSearch] = useState("");

  // Series options for autocomplete
  const [seriesOptions, setSeriesOptions] = useState([]);

  // Royalty rates (book-level, not per-author)
  const [distributorRoyaltyRate, setDistributorRoyaltyRate] = useState("50");
  const [handSoldRoyaltyRate, setHandSoldRoyaltyRate] = useState("20");

  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState(null);

  // Load authors and series options
  useEffect(() => {
    let cancelled = false;

    async function load() {
      setAuthorsLoading(true);
      setAuthorsErr(null);
      try {
        const [authorsData, seriesData] = await Promise.all([
          booksApi.listAuthors(),
          booksApi.listSeries().catch(() => []),
        ]);
        if (!cancelled) {
          setAuthorOptions(Array.isArray(authorsData) ? authorsData : []);
          setSeriesOptions(Array.isArray(seriesData) ? seriesData : []);
        }
      } catch (e) {
        if (!cancelled) setAuthorsErr(errorMessage(e));
      } finally {
        if (!cancelled) setAuthorsLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, []);

  async function onSubmit(e) {
    e.preventDefault();
    setErr(null);
    setSubmitting(true);

    try {
      if (!selectedAuthorId) {
        setErr(
          authorSearch.trim()
            ? `Author "${authorSearch.trim()}" does not exist.`
            : "Author field may not be empty."
        );
        return;
      }

      const coverPriceCents = Math.round(parseFloat(coverPrice) * 100);
      const printCostCents = Math.round(parseFloat(printCost) * 100);
      if (!isNaN(coverPriceCents) && !isNaN(printCostCents) && coverPriceCents < printCostCents) {
        setErr("Cover price must be equal to or greater than the print cost.");
        return;
      }

      // Upload cover image first if a new file was selected
      let finalCoverImagePath = coverImagePath.trim() === "" ? null : coverImagePath.trim();
      
      if (coverImageFile) {
        const uploadResult = await booksApi.uploadCoverImage(coverImageFile);
        finalCoverImagePath = uploadResult.cover_image_path;
      }

      const payload = {
        title: title.trim(),
        publication_date: publicationMonth,
        isbn_13: cleanIsbn(isbn13),
        isbn_10: cleanIsbn(isbn10) === "" ? null : cleanIsbn(isbn10),
        author_id: selectedAuthorId ? Number(selectedAuthorId) : null,
        distributor_author_royalty_rate: String(parseFloat(distributorRoyaltyRate) / 100),
        hand_sold_author_royalty_rate: String(parseFloat(handSoldRoyaltyRate) / 100),
        cover_price: coverPrice,
        print_cost: printCost,
        series_name: seriesName.trim() === "" ? null : seriesName.trim(),
        series_position: seriesName.trim() === "" || seriesPosition === "" ? null : Number(seriesPosition),
        cover_image_path: finalCoverImagePath,
        amazon_asin_ebook: amazonAsin.trim() === "" ? null : amazonAsin.trim().toUpperCase(),
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
            <form onSubmit={onSubmit}>
              {authorsErr && <ErrorAlert className="mb-5">Failed to load authors: {authorsErr}</ErrorAlert>}

              <div className="divide-y divide-slate-100">
                {/* Title & Author — no section header, mirrors edit mode */}
                <div className="pb-5 space-y-4">
                  <FormField label="Title">
                    <Input
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      className="text-lg font-semibold"
                      required
                    />
                  </FormField>
                  <div className="flex items-end gap-3">
                    <div className="flex-1 min-w-0">
                      <AuthorPicker
                        authorOptions={authorOptions}
                        selectedAuthorId={selectedAuthorId}
                        setSelectedAuthorId={setSelectedAuthorId}
                        authorSearch={authorSearch}
                        setAuthorSearch={setAuthorSearch}
                        required
                      />
                    </div>
                    <Button
                      type="button"
                      className="shrink-0 whitespace-nowrap"
                      onClick={() => nav("/authors/create", { state: { returnTo: "/books/input" } })}
                    >
                      New Author
                    </Button>
                  </div>
                </div>

                {/* Series */}
                <div className="py-5">
                  <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Series
                  </p>
                  <SeriesPicker
                    seriesName={seriesName}
                    setSeriesName={setSeriesName}
                    seriesPosition={seriesPosition}
                    setSeriesPosition={setSeriesPosition}
                    seriesOptions={seriesOptions}
                    originalSeriesName={null}
                  />
                </div>

                {/* Publication Info */}
                <div className="py-5">
                  <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Publication Info
                  </p>
                  <div className="space-y-4">
                    <MonthPicker
                      label="Publication month, year"
                      value={publicationMonth}
                      onChange={setPublicationMonth}
                      required
                    />
                    <div className="grid grid-cols-2 gap-4">
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
                    <FormField label="Amazon ASIN — ebook (optional)">
                      <Input
                        value={amazonAsin}
                        onChange={(e) => setAmazonAsin(e.target.value.toUpperCase())}
                        placeholder="e.g. B09XYZ1234"
                        maxLength={10}
                      />
                      <p className="mt-1 text-xs text-slate-400">
                        10-character alphanumeric identifier from Amazon (e.g. B09XYZ1234).
                      </p>
                    </FormField>
                  </div>
                </div>

                {/* Pricing */}
                <div className="py-5">
                  <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Pricing
                  </p>
                  <div className="grid grid-cols-2 gap-4">
                    <FormField label="Cover price ($)">
                      <Input
                        type="number"
                        min="0"
                        step="0.01"
                        value={coverPrice}
                        onChange={(e) => setCoverPrice(e.target.value)}
                        placeholder="19.99"
                        required
                      />
                    </FormField>
                    <FormField label="Print cost ($)">
                      <Input
                        type="number"
                        min="0"
                        step="0.01"
                        value={printCost}
                        onChange={(e) => setPrintCost(e.target.value)}
                        placeholder="4.25"
                        required
                      />
                    </FormField>
                  </div>
                </div>

                {/* Royalty Rates */}
                <div className="py-5">
                  <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Royalty Rates
                  </p>
                  <div className="grid grid-cols-2 gap-4">
                    <FormField label="Distributor royalty rate (%)">
                      <Input
                        type="number"
                        min="0"
                        max="100"
                        step="1"
                        value={distributorRoyaltyRate}
                        onChange={(e) => setDistributorRoyaltyRate(e.target.value)}
                        required
                      />
                      <p className="mt-1 text-xs text-slate-400">
                        Changes only affect future sales.
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
                        required
                      />
                      <p className="mt-1 text-xs text-slate-400">
                        Changes only affect future sales.
                      </p>
                    </FormField>
                  </div>
                </div>

                {/* Cover Image */}
                <div className="pt-5">
                  <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Cover Image
                  </p>
                  <CoverImageField
                    value={coverImagePath}
                    onChange={setCoverImagePath}
                    onFileChange={setCoverImageFile}
                    title={title}
                    label=""
                  />
                </div>
              </div>

              {/* Error message */}
              {err && <ErrorAlert className="mt-5">{err}</ErrorAlert>}

              {/* Actions */}
              <div className="mt-5 flex items-center justify-end gap-2">
                <Button type="button" variant="secondary" onClick={() => nav("/books")}>
                  Cancel
                </Button>
                <Button disabled={submitting} className="min-w-[120px]">
                  {submitting ? "Creating..." : "Create"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
