interface ConfirmDialogProps {
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  message,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      data-testid="confirm-dialog"
    >
      <div className="mx-4 w-full max-w-sm rounded-lg bg-bg-surface border border-border-default p-6">
        <p className="text-sm text-text-primary">{message}</p>
        <div className="mt-4 flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="rounded-md bg-bg-elevated px-4 py-2 text-sm text-text-secondary hover:bg-bg-overlay"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="rounded-md bg-status-blocked px-4 py-2 text-sm text-text-primary hover:bg-red-600"
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
}
