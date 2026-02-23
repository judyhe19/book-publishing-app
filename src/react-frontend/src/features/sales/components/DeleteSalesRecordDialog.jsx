// src/features/sales/components/DeleteSalesRecordDialog.jsx
import React from "react";
import { ConfirmDialog, ErrorAlert } from "../../../shared/components";

export default function DeleteSalesRecordDialog({
  open,
  onConfirm,
  onCancel,
  saleId,
  disabled,
}) {
  return (
    <ConfirmDialog
      open={open}
      title="Delete sales record?"
      confirmText="Delete"
      confirmVariant="danger"
      confirming={disabled}
      onCancel={onCancel}
      onConfirm={onConfirm}
    >
      <div className="space-y-3">
        <ErrorAlert>This action cannot be undone.</ErrorAlert>
        <p className="text-slate-600">
          This will permanently delete Sales Record #{saleId}.
        </p>
      </div>
    </ConfirmDialog>
  );
}
