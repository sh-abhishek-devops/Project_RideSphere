import { Button } from "./Button";

interface ErrorDisplayProps {
  title?: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function ErrorDisplay({
  actionLabel = "Try again",
  message,
  onAction,
  title = "Something went wrong"
}: ErrorDisplayProps) {
  return (
    <div className="error-display" role="alert">
      <h3>{title}</h3>
      <p>{message}</p>
      {onAction ? (
        <Button onClick={onAction} type="button" variant="secondary">
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}
