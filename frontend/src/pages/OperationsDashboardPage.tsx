import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { getErrorMessage } from "api/client";
import { Button } from "components/Button";
import { ErrorDisplay } from "components/ErrorDisplay";
import { fetchHealthStatus } from "services/healthService";
import { getOperationsDashboardMetrics } from "services/operationsService";
import { formatDateTime, formatRelativeCount } from "utils/app";

export function OperationsDashboardPage() {
  const [filters, setFilters] = useState({
    dateFrom: "",
    dateTo: ""
  });
  const [submittedFilters, setSubmittedFilters] = useState({
    dateFrom: "",
    dateTo: ""
  });
  const [validationError, setValidationError] = useState("");

  const healthQuery = useQuery({
    queryKey: ["health-status"],
    queryFn: fetchHealthStatus
  });

  const metricsQuery = useQuery({
    queryKey: ["operations-dashboard", submittedFilters],
    queryFn: () => getOperationsDashboardMetrics(submittedFilters)
  });

  function handleApplyFilters(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (filters.dateFrom && filters.dateTo && filters.dateTo < filters.dateFrom) {
      setValidationError("End date must be on or after the start date.");
      return;
    }

    setValidationError("");
    setSubmittedFilters(filters);
  }

  function handleResetFilters() {
    setFilters({ dateFrom: "", dateTo: "" });
    setSubmittedFilters({ dateFrom: "", dateTo: "" });
    setValidationError("");
  }

  if (metricsQuery.isLoading || healthQuery.isLoading) {
    return <div className="panel"><p>Loading operations workspace...</p></div>;
  }

  if (metricsQuery.isError || !metricsQuery.data) {
    return (
      <ErrorDisplay
        message={metricsQuery.error ? getErrorMessage(metricsQuery.error) : "Unable to load operations metrics."}
        onAction={() => metricsQuery.refetch()}
      />
    );
  }

  if (healthQuery.isError || !healthQuery.data) {
    return <ErrorDisplay message="Unable to load platform health." onAction={() => healthQuery.refetch()} />;
  }

  const metrics = metricsQuery.data;

  return (
    <section className="page">
      <div className="page__header">
        <div>
          <p className="eyebrow">Operations dashboard</p>
          <h1>Monitor platform throughput, supply, payments, and support workload.</h1>
        </div>
      </div>

      <article className="panel">
        <div className="panel__header">
          <h2>Filters</h2>
          <p className="inline-muted">All metrics are calculated server-side using aggregated database queries.</p>
        </div>
        <form className="filter-form" onSubmit={handleApplyFilters}>
          <label className="field">
            <span className="field__label">Start date</span>
            <input
              className="input"
              onChange={(event) => setFilters((current) => ({ ...current, dateFrom: event.target.value }))}
              type="date"
              value={filters.dateFrom}
            />
          </label>
          <label className="field">
            <span className="field__label">End date</span>
            <input
              className="input"
              onChange={(event) => setFilters((current) => ({ ...current, dateTo: event.target.value }))}
              type="date"
              value={filters.dateTo}
            />
          </label>
          <div className="panel__actions">
            <Button type="submit" variant="primary">
              Apply filters
            </Button>
            <Button onClick={handleResetFilters} type="button" variant="ghost">
              Reset
            </Button>
          </div>
        </form>
        {validationError ? <ErrorDisplay message={validationError} title="Invalid filter range" /> : null}
      </article>

      <div className="stats-grid">
        <MetricCard label="Total ride requests" value={metrics.total_ride_requests} description={formatRelativeCount(metrics.total_ride_requests, "request")} />
        <MetricCard
          label="Searching for drivers"
          value={metrics.rides_searching_for_drivers}
          description="Ride requests still waiting on supply."
        />
        <MetricCard label="Active trips" value={metrics.active_trips} description="Trips still in progress." />
        <MetricCard label="Completed trips" value={metrics.completed_trips} description="Trips that reached completion." />
        <MetricCard label="Cancelled rides" value={metrics.cancelled_rides} description="Ride requests cancelled in the selected range." />
        <MetricCard label="Available drivers" value={metrics.available_drivers} description="Latest availability records marked available." />
        <MetricCard
          label="Drivers on trips"
          value={metrics.drivers_currently_on_trips}
          description="Latest availability records marked on trip."
        />
        <MetricCard label="Payment successes" value={metrics.payment_successes} description="Successful mock payments created in range." />
        <MetricCard label="Payment failures" value={metrics.payment_failures} description="Failed mock payments created in range." />
        <MetricCard label="Open support cases" value={metrics.open_support_cases} description="Support cases not yet resolved." />
      </div>

      <div className="content-grid">
        <article className="panel">
          <div className="panel__header">
            <h2>Platform health</h2>
          </div>
          <div className="ride-summary">
            <div className="ride-summary__row">
              <span>Application</span>
              <strong>{healthQuery.data.application}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Health status</span>
              <strong>{healthQuery.data.status}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Database status</span>
              <strong>{healthQuery.data.database?.status ?? "Unknown"}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Generated</span>
              <strong>{formatDateTime(metrics.generated_at)}</strong>
            </div>
          </div>
        </article>

        <article className="panel">
          <div className="panel__header">
            <h2>Filter summary</h2>
          </div>
          <div className="ride-summary">
            <div className="ride-summary__row">
              <span>Start date</span>
              <strong>{metrics.date_from ?? "Not set"}</strong>
            </div>
            <div className="ride-summary__row">
              <span>End date</span>
              <strong>{metrics.date_to ?? "Not set"}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Payments observed</span>
              <strong>{metrics.payment_successes + metrics.payment_failures}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Open operational backlog</span>
              <strong>{metrics.rides_searching_for_drivers + metrics.open_support_cases}</strong>
            </div>
          </div>
        </article>
      </div>
    </section>
  );
}

function MetricCard({ description, label, value }: { description: string; label: string; value: number }) {
  return (
    <article className="stat-card">
      <span>{label}</span>
      <strong>{value}</strong>
      <p>{description}</p>
    </article>
  );
}
