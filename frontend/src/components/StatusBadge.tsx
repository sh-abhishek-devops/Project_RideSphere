import { formatStatusLabel } from "utils/app";

interface StatusBadgeProps {
  status: string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const normalized = status.toLowerCase();
  const tone = normalized.includes("completed") || normalized.includes("success")
    ? "success"
    : normalized.includes("failed") || normalized.includes("cancelled") || normalized.includes("offline")
      ? "danger"
      : normalized.includes("searching") || normalized.includes("processing") || normalized.includes("reserved")
        ? "warning"
        : "info";

  return <span className={`status-badge status-badge--${tone}`}>{formatStatusLabel(status)}</span>;
}
