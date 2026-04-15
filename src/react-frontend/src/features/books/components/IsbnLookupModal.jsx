// src/features/books/components/IsbnLookupModal.jsx
import React, { useState, useEffect } from "react";
import { Button, ErrorAlert, Input } from "../../../shared/components";
import { errorMessage } from "../../../shared/utils/errors";
import { lookupIsbn } from "../api/isbnApi";

/**
 * Modal for looking up book metadata by ISBN-10 or ISBN-13.
 *
 * Props:
 *   open        boolean
 *   onClose     fn
 *   onSuccess   fn(data)  — called with normalized lookup data; modal closes automatically
 */
export default function IsbnLookupModal({ open, onClose, onSuccess }) {
  const [isbn, setIsbn] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  // Reset state when modal opens
  useEffect(() => {
    if (open) {
      setIsbn("");
      setErr(null);
      setLoading(false);
    }
  }, [open]);

  if (!open) return null;

  async function handleLookup(e) {
    e.preventDefault();
    const trimmed = isbn.trim();
    if (!trimmed) return;

    setErr(null);
    setLoading(true);
    try {
      const data = await lookupIsbn(trimmed);
      onSuccess(data);
      onClose();
    } catch (e) {
      setErr(errorMessage(e));
    } finally {
      setLoading(false);
    }
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
      <div className="relative w-full max-w-sm rounded-2xl bg-white shadow-xl border border-slate-200 flex flex-col">
        {/* Header */}
        <div className="p-5 border-b border-slate-100">
          <div className="text-lg font-semibold text-slate-900">Import from ISBN</div>
          <p className="mt-1 text-sm text-slate-500">
            Enter an ISBN-13 or ISBN-10 to pre-fill the book form.
          </p>
        </div>

        {/* Body */}
        <form onSubmit={handleLookup}>
          <div className="p-5 flex flex-col gap-4">
            {err && <ErrorAlert>{err}</ErrorAlert>}

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                ISBN
              </label>
              <Input
                value={isbn}
                onChange={(e) => setIsbn(e.target.value)}
                placeholder="e.g. 9780060850524 or 0060850523"
                autoFocus
                disabled={loading}
              />
            </div>
          </div>

          {/* Footer */}
          <div className="px-5 pb-5 flex items-center justify-end gap-2">
            <Button type="button" variant="secondary" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={loading || !isbn.trim()}
              className="min-w-[100px]"
            >
              {loading ? "Looking up…" : "Look Up"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
