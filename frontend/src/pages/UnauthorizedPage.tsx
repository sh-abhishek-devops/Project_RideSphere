import { Link } from "react-router-dom";

export function UnauthorizedPage() {
  return (
    <main className="standalone-page">
      <section className="standalone-card">
        <p className="eyebrow">Unauthorized</p>
        <h1>That area is outside your current access scope.</h1>
        <p>Use a route that matches your assigned role, or sign in with a different account.</p>
        <Link className="button button--primary" to="/login">
          Return to sign in
        </Link>
      </section>
    </main>
  );
}
