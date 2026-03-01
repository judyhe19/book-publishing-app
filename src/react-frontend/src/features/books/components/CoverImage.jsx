// src/features/books/components/CoverImage.jsx
import React, { useState } from "react";

/**
 * Displays a book cover image with fallback for missing/errored images.
 */
export default function CoverImage({ path, title, className = "" }) {
  const [errored, setErrored] = useState(false);

  if (!path || errored) {
    return (
      <div
        className={`flex h-64 w-48 flex-shrink-0 items-center justify-center rounded-lg border-2 border-dashed border-slate-200 bg-slate-50 text-center text-xs text-slate-400 ${className}`}
      >
        No cover art
      </div>
    );
  }

  // Stored covers are served via the API endpoint; local blob/data previews are used directly.
  const src = path.startsWith("/static/")
    ? `/api/books/cover-image/?path=${encodeURIComponent(path)}`
    : path;

  return (
    <img
      src={src}
      alt={`Cover of ${title}`}
      className={`h-64 w-auto max-w-[12rem] flex-shrink-0 rounded-lg object-cover shadow-md ${className}`}
      onError={() => setErrored(true)}
    />
  );
}
