import { Button } from "../../../shared/components/Button";

export default function ConfirmDialog({ open, title, body, onCancel, onConfirm, confirming }) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
        <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
        <p className="text-slate-600 mt-2">{body}</p>

        <div className="flex justify-end gap-2 mt-6">
          <Button variant="secondary" onClick={onCancel} disabled={confirming}>
            Cancel
          </Button>
          <Button onClick={onConfirm} disabled={confirming}>
            {confirming ? "Marking..." : "Confirm"}
          </Button>
        </div>
      </div>
    </div>
  );
}
