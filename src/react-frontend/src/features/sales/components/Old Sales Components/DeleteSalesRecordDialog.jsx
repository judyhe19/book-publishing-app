import React from "react";

import ConfirmDialog from "./ConfirmDialog";

export default function DeleteSalesRecordDialog({
  open,
  onOpenChange,
  onConfirm,
  onCancel,
  saleId,
  disabled,
}) {
  return (
    <ConfirmDialog
      open={open}
      onOpenChange={onOpenChange}
      title="Delete sales record?"
      description={`This will permanently delete Sales Record #${saleId}. This cannot be undone.`}
      confirmText="Delete"
      confirmVariant="danger"
      onConfirm={onConfirm}
      onCancel={onCancel}
      disabled={disabled}
    />
  );
}
