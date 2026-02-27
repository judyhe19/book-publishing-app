// src/features/author/components/DeleteAuthorDialog.jsx
import React from "react";
import { ConfirmDialog, ErrorAlert } from "../../../shared/components";

export default function DeleteAuthorDialog({
  open,
  onConfirm,
  onCancel,
  authorName,
  authorEmail,
  books = [],
  hasSales = false,
  deletionBehaviorText,
  disabled,
}) {
  const safeBooks = Array.isArray(books) ? books : [];

  return (
    <ConfirmDialog
      open={open}
      title="Delete author?"
      confirmText="Delete"
      confirmVariant="danger"
      confirming={disabled}
      onCancel={onCancel}
      onConfirm={onConfirm}
    >
      <div className="space-y-3">
        <ErrorAlert>
          This action cannot be undone.
          {hasSales ? (
            <span className="block mt-1 font-medium">
              Note: sales records exist for one or more books by this author.
            </span>
          ) : null}
        </ErrorAlert>

        <p className="text-slate-600">
          This will permanently delete <span className="font-medium">{authorName}</span>
          {authorEmail ? (
            <>
              {" "}
              (<span className="font-medium">{authorEmail}</span>)
            </>
          ) : null}
          .
        </p>

        <div>
          <div className="text-sm font-medium text-slate-900">Book title(s)</div>
          {safeBooks.length === 0 ? (
            <div className="text-slate-500 text-sm mt-1">No books found for this author.</div>
          ) : (
            <ul className="mt-1 list-disc pl-5 text-slate-700 text-sm space-y-1">
              {safeBooks.map((b) => (
                <li key={b.id || b.title}>
                  {b.title || "Untitled"}
                  {b?.has_sales_records || Number(b?.sales_count ?? 0) > 0 ? (
                    <span className="ml-2 text-xs font-medium text-red-700">
                      (sales exist)
                    </span>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </div>

        <p className="text-slate-600 text-sm">
          {deletionBehaviorText ||
            "The system will make clear what happens to historical records after deletion."}
        </p>
      </div>
    </ConfirmDialog>
  );
}