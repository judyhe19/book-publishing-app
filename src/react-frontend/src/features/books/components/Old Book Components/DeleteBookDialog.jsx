import React from "react";
import { ConfirmDialog } from "./ConfirmDialog";

export function DeleteBookDialog({ open, book, deleting, onCancel, onConfirm }) {
  const hasSales = (book?.total_sales_to_date ?? 0) > 0;

  return (
    <ConfirmDialog
      open={open}
      title="Delete book?"
      confirmText={deleting ? "Deleting..." : "Delete"}
      confirmDisabled={deleting}
      onCancel={onCancel}
      onConfirm={onConfirm}
    >
      <div className="space-y-3">
        <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          This action cannot be undone.
        </div>

        <div>
          <div className="text-xs font-semibold uppercase text-slate-500">Title</div>
          <div className="text-slate-900 font-semibold">{book?.title}</div>
        </div>

        <div>
          <div className="text-xs font-semibold uppercase text-slate-500">Author(s)</div>
          <div className="text-slate-900">
            {(book?.authors || []).length === 0
              ? "—"
              : book.authors.map((a) => a.name).join(", ")}
          </div>
        </div>

        {hasSales ? (
          <div className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            <span className="font-semibold">Warning:</span> This book has existing sales
            records (Total Sales: {book?.total_sales_to_date}). Deleting will delete all existing sales for this book.
          </div>
        ) : (
          <div className="text-sm text-slate-600">
            No sales records have been recorded for this book.
          </div>
        )}

        <div className="text-sm text-slate-700">
          Click <span className="font-semibold">Delete</span> again to confirm.
        </div>
      </div>
    </ConfirmDialog>
  );
}
