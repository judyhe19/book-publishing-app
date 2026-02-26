// src/features/books/components/BookEditMode.jsx
import React from "react";
import { FormField, Input, MonthPicker } from "../../../shared/components";
import CoverImageField from "./CoverImageField";
import AuthorPicker from "./AuthorPicker";
import SeriesFields from "./SeriesFields";

/**
 * Edit form for book details.
 * Used in BookDetailPage when in edit mode.
 */
export default function BookEditMode({
  // Basic fields
  title,
  setTitle,
  publicationMonth,
  setPublicationMonth,
  isbn13,
  setIsbn13,
  isbn10,
  setIsbn10,
  // Author
  authorOptions,
  selectedAuthorId,
  setSelectedAuthorId,
  authorSearch,
  setAuthorSearch,
  // Royalty rates
  distributorRoyaltyRate,
  setDistributorRoyaltyRate,
  handSoldRoyaltyRate,
  setHandSoldRoyaltyRate,
  // Pricing
  coverPrice,
  setCoverPrice,
  printCost,
  setPrintCost,
  // Cover image
  coverImagePath,
  setCoverImagePath,
  onCoverImageFileChange,
  // Series
  seriesName,
  setSeriesName,
  seriesPosition,
  setSeriesPosition,
}) {
  return (
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

      <AuthorPicker
        authorOptions={authorOptions}
        selectedAuthorId={selectedAuthorId}
        setSelectedAuthorId={setSelectedAuthorId}
        authorSearch={authorSearch}
        setAuthorSearch={setAuthorSearch}
      />

      {/* Royalty rates */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <FormField label="Distributor royalty rate">
          <Input
            type="number"
            min="0"
            max="1"
            step="0.01"
            value={distributorRoyaltyRate}
            onChange={(e) => setDistributorRoyaltyRate(e.target.value)}
          />
          <p className="mt-1 text-xs text-slate-400">
            Decimal (0–1). Changes only affect future sales.
          </p>
        </FormField>
        <FormField label="Hand-sold royalty rate">
          <Input
            type="number"
            min="0"
            max="1"
            step="0.01"
            value={handSoldRoyaltyRate}
            onChange={(e) => setHandSoldRoyaltyRate(e.target.value)}
          />
          <p className="mt-1 text-xs text-slate-400">
            Decimal (0–1). Changes only affect future sales.
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
      <CoverImageField
        value={coverImagePath}
        onChange={setCoverImagePath}
        onFileChange={onCoverImageFileChange}
        title={title}
      />

      {/* Series */}
      <SeriesFields
        seriesName={seriesName}
        setSeriesName={setSeriesName}
        seriesPosition={seriesPosition}
        setSeriesPosition={setSeriesPosition}
      />
    </div>
  );
}
