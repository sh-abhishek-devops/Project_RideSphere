import { useHealthStatus } from "../hooks/useHealthStatus";

export function HomePage() {
  const { data, isLoading, isError } = useHealthStatus();

  return (
    <main className="home-page">
      <section className="hero">
        <p className="eyebrow">Operational Foundation</p>
        <h1>RideSphere</h1>
        <p className="subtitle">Ride Operations and Trip Management Platform</p>
      </section>

      <section className="status-card" aria-live="polite">
        <h2>Backend Status</h2>
        {isLoading && <p>Checking backend health...</p>}
        {isError && <p>Backend unavailable</p>}
        {data && (
          <dl className="status-grid">
            <div>
              <dt>Application</dt>
              <dd>{data.application}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>{data.status}</dd>
            </div>
          </dl>
        )}
      </section>
    </main>
  );
}
