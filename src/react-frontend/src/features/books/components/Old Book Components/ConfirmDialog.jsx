import React from "react";
import { Button } from "../../../shared/components/Button";

export function ConfirmDialog({
  open,
  title,
  children,
  confirmText = "Confirm",
  confirmDisabled = false,
  onCancel,
  onConfirm,
}) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 bg-black/40"
        onClick={onCancel}
        aria-label="Close dialog"
      />

      <div className="relative w-full max-w-lg rounded-2xl bg-white shadow-xl border border-slate-200">
        <div className="p-5 border-b border-slate-100">
          <div className="text-lg font-semibold text-slate-900">{title}</div>
        </div>

        <div className="p-5">{children}</div>

        <div className="p-5 pt-0 flex items-center justify-end gap-2">
          <Button variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
          <Button disabled={confirmDisabled} onClick={onConfirm}>
            {confirmText}
          </Button>
        </div>
      </div>
    </div>
  );
}
