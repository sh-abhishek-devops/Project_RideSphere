import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <main className="standalone-page">
      <section className="standalone-card">
        <p className="eyebrow">Not found</p>
        <h1>The page you requested does not exist.</h1>
        <p>Use the application navigation to return to a working route.</p>
        <Link className="button button--primary" to="/login">
          Go to login
        </Link>
      </section>
    </main>
  );
}
