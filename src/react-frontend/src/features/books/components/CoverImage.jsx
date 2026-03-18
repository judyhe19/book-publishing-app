// src/features/books/components/CoverImage.jsx
import { useState } from "react";

/**
 * Displays a book cover image with fallback for missing/errored images.
 * Pass className to control size (default: "h-64 w-48").
 */
export default function CoverImage({ path, title, className = "h-64 w-48" }) {
  const [errored, setErrored] = useState(false);

  if (!path || errored) {
    return (
      <div
        className={`flex flex-shrink-0 items-center justify-center rounded-lg border-2 border-dashed border-slate-200 bg-slate-50 text-center text-xs text-slate-400 ${className}`}
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
      className={`flex-shrink-0 rounded-lg object-cover shadow-md ${className}`}
      onError={() => setErrored(true)}
    />
  );
}
