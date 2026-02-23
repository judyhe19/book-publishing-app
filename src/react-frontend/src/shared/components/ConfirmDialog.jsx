// src/shared/components/ConfirmDialog.jsx
import React from "react";
import { Button } from "./Button";

/**
 * Unified confirmation dialog.
 * Supports both simple string body and complex JSX children.
 * 
 * Props:
 * - open: Whether the dialog is visible
 * - title: Dialog title
 * - body: Simple string content (ignored if children provided)
 * - children: Complex JSX content (takes precedence over body)
 * - confirmText: Text for confirm button (default: "Confirm")
 * - confirmVariant: Button variant for confirm ("primary" | "danger")
 * - confirming: Loading state - disables buttons and shows loading text
 * - onCancel: Cancel handler
 * - onConfirm: Confirm handler
 */
export function ConfirmDialog({
  open,
  title,
  body,
  children,
  confirmText = "Confirm",
  confirmVariant = "primary",
  confirming = false,
  onCancel,
  onConfirm,
}) {
  if (!open) return null;

  const content = children || (body && <p className="text-slate-600">{body}</p>);
  const buttonText = confirming ? `${confirmText.replace(/\.\.\.$/, "")}...` : confirmText;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <button
        type="button"
        className="absolute inset-0 bg-black/40"
        onClick={onCancel}
        aria-label="Close dialog"
      />

      {/* Dialog */}
      <div className="relative w-full max-w-lg rounded-2xl bg-white shadow-xl border border-slate-200">
        {/* Header */}
        <div className="p-5 border-b border-slate-100">
          <div className="text-lg font-semibold text-slate-900">{title}</div>
        </div>

        {/* Body */}
        <div className="p-5">{content}</div>

        {/* Footer */}
        <div className="p-5 pt-0 flex items-center justify-end gap-2">
          <Button variant="secondary" onClick={onCancel} disabled={confirming}>
            Cancel
          </Button>
          <Button 
            variant={confirmVariant} 
            disabled={confirming} 
            onClick={onConfirm}
          >
            {buttonText}
          </Button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmDialog;
