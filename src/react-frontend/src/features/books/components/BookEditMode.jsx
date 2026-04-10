// src/features/books/components/BookEditMode.jsx
import { FormField, Input, MonthPicker } from "../../../shared/components";
import CoverImageField from "./CoverImageField";
import AuthorPicker from "./AuthorPicker";
import SeriesPicker from "./SeriesPicker";

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
  // Amazon
  amazonAsin,
  setAmazonAsin,
  // Kickstarter tags
  kickstarterTagEbook,
  setKickstarterTagEbook,
  kickstarterTagPrint,
  setKickstarterTagPrint,
  // Release status
  released,
  setReleased,
  // Series
  seriesName,
  setSeriesName,
  seriesPosition,
  setSeriesPosition,
  seriesOptions,
  originalSeriesName,
}) {
  return (
    <div className="mt-4">
      {/* Two-column: cover art left, fields right */}
      <div className="flex flex-col gap-8 sm:flex-row">
        {/* Cover image */}
        <div className="flex-shrink-0">
          <CoverImageField
            value={coverImagePath}
            onChange={setCoverImagePath}
            onFileChange={onCoverImageFileChange}
            title={title}
            imageClassName="h-[30rem] w-80"
          />
        </div>

        {/* Grouped fields */}
        <div className="flex-1 divide-y divide-slate-100">
          {/* Title & Author - mirrors the page header shown in view mode */}
          <div className="pb-5 space-y-4">
            <FormField label="Title">
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="text-lg font-semibold"
                required
              />
            </FormField>
            <AuthorPicker
              authorOptions={authorOptions}
              selectedAuthorId={selectedAuthorId}
              setSelectedAuthorId={setSelectedAuthorId}
              authorSearch={authorSearch}
              setAuthorSearch={setAuthorSearch}
              required
            />
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
              seriesOptions={seriesOptions || []}
              originalSeriesName={originalSeriesName}
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
                  <Input value={isbn13} onChange={(e) => setIsbn13(e.target.value)} required/>
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
              <div className="grid grid-cols-2 gap-4">
                <FormField label="Kickstarter tag — ebook (optional)">
                  <Input
                    value={kickstarterTagEbook}
                    onChange={(e) => setKickstarterTagEbook(e.target.value)}
                    placeholder="e.g. ebook-the-hobbit"
                    maxLength={128}
                  />
                </FormField>
                <FormField label="Kickstarter tag — print (optional)">
                  <Input
                    value={kickstarterTagPrint}
                    onChange={(e) => setKickstarterTagPrint(e.target.value)}
                    placeholder="e.g. paperback-the-hobbit"
                    maxLength={128}
                  />
                </FormField>
              </div>
              <div>
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <span className="text-sm font-medium text-slate-700">Released</span>
                  <input
                    type="checkbox"
                    checked={released}
                    onChange={(e) => setReleased(e.target.checked)}
                    className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                  />
                </label>
              </div>
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
                  required
                />
              </FormField>
            </div>
          </div>

          {/* Royalty Rates */}
          <div className="pt-5">
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
        </div>
      </div>
    </div>
  );
}
