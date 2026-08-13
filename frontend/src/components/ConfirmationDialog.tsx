import { Button } from "./Button";
import { Modal } from "./Modal";

interface ConfirmationDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  confirmVariant?: "primary" | "secondary" | "ghost" | "danger";
  isSubmitting?: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

export function ConfirmationDialog({
  confirmLabel = "Confirm",
  confirmVariant = "danger",
  isOpen,
  isSubmitting = false,
  message,
  onCancel,
  onConfirm,
  title
}: ConfirmationDialogProps) {
  return (
    <Modal
      footer={
        <>
          <Button onClick={onCancel} type="button" variant="ghost">
            Keep editing
          </Button>
          <Button isLoading={isSubmitting} onClick={onConfirm} type="button" variant={confirmVariant}>
            {confirmLabel}
          </Button>
        </>
      }
      isOpen={isOpen}
      onClose={onCancel}
      title={title}
    >
      <p>{message}</p>
    </Modal>
  );
}
