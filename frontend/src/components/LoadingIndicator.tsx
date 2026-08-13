interface LoadingIndicatorProps {
  label?: string;
}

export function LoadingIndicator({ label = "Loading data..." }: LoadingIndicatorProps) {
  return (
    <div className="loading-state" role="status">
      <span className="loading-state__spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
