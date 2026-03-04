// src/features/books/components/DeleteBookDialog.jsx
import React from "react";
import { ConfirmDialog, ErrorAlert, DetailField } from "../../../shared/components";

export function DeleteBookDialog({ open, book, deleting, onCancel, onConfirm }) {
  const hasSales = (book?.total_sales_to_date ?? 0) > 0;

  return (
    <ConfirmDialog
      open={open}
      title="Delete book?"
      confirmText="Delete"
      confirmVariant="danger"
      confirming={deleting}
      onCancel={onCancel}
      onConfirm={onConfirm}
    >
      <div className="space-y-3">
        <ErrorAlert>This action cannot be undone.</ErrorAlert>

        <DetailField label="Title">
          <span className="font-semibold">{book?.title}</span>
        </DetailField>

        <DetailField label="Author">
          {book?.author_name ?? "—"}
        </DetailField>

        {hasSales ? (
          <ErrorAlert variant="warning">
            <span className="font-semibold">Warning:</span> This book has existing sales
            records (Total Sales: {book?.total_sales_to_date}). Deleting will delete all
            existing sales for this book.
          </ErrorAlert>
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

export default DeleteBookDialog;
