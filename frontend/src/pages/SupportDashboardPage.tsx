import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { ErrorDisplay } from "components/ErrorDisplay";
import { LoadingIndicator } from "components/LoadingIndicator";
import { StatusBadge } from "components/StatusBadge";
import { listSupportCases } from "services/supportCaseService";
import { formatDateTime, formatStatusLabel } from "utils/app";

export function SupportDashboardPage() {
  const casesQuery = useQuery({
    queryKey: ["support-cases"],
    queryFn: listSupportCases,
    refetchInterval: 10000
  });

  if (casesQuery.isLoading) {
    return <LoadingIndicator label="Loading support cases..." />;
  }

  if (casesQuery.isError) {
    return <ErrorDisplay message="Unable to load support cases." onAction={() => casesQuery.refetch()} />;
  }

  const cases = casesQuery.data ?? [];
  const openCases = cases.filter((item) => item.status !== "RESOLVED");
  const criticalCases = openCases.filter((item) => item.priority === "CRITICAL");

  return (
    <section className="page">
      <div className="page__header">
        <div>
          <p className="eyebrow">Support cases</p>
          <h1>Investigate live ride issues and move each case toward resolution.</h1>
        </div>
      </div>

      <div className="stats-grid">
        <article className="stat-card">
          <span>Total cases</span>
          <strong>{cases.length}</strong>
          <p>All support cases returned by the backend.</p>
        </article>
        <article className="stat-card">
          <span>Open cases</span>
          <strong>{openCases.length}</strong>
          <p>Cases that still need agent action.</p>
        </article>
        <article className="stat-card">
          <span>Critical priority</span>
          <strong>{criticalCases.length}</strong>
          <p>Cases marked for urgent follow-up.</p>
        </article>
      </div>

      <article className="panel">
        <div className="panel__header">
          <h2>Case queue</h2>
          <p className="inline-muted">Cases are ordered by most recently updated records from the support API.</p>
        </div>
        <div className="list">
          {cases.map((supportCase) => (
            <article className="list__card" key={supportCase.id}>
              <div className="list__card-header">
                <div>
                  <h2>{supportCase.issue_summary}</h2>
                  <p>{formatDateTime(supportCase.updated_at)}</p>
                </div>
                <StatusBadge status={supportCase.status} />
              </div>
              <div className="list__meta">
                <span>Priority: {formatStatusLabel(supportCase.priority)}</span>
                <span>Assigned: {supportCase.assigned_agent_user?.email ?? "Unassigned"}</span>
              </div>
              <div className="panel__actions">
                <Link className="button button--ghost" to={`/support/investigations/${supportCase.id}`}>
                  Investigate ride
                </Link>
                <Link className="button button--primary" to={`/support/cases/${supportCase.id}`}>
                  Open case
                </Link>
              </div>
            </article>
          ))}
          {cases.length === 0 ? <p className="empty-state">No support cases have been created yet.</p> : null}
        </div>
      </article>
    </section>
  );
}
