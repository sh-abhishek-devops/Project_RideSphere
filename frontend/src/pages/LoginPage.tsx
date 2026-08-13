import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { getErrorMessage } from "api/client";
import { Button } from "components/Button";
import { ErrorDisplay } from "components/ErrorDisplay";
import { Form } from "components/Form";
import { Input } from "components/Input";
import { useAuth } from "hooks/useAuth";
import { getDefaultRouteForRole } from "utils/app";

export function LoginPage() {
  const auth = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const envelope = await auth.login({ email, password });
      const destination =
        (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ??
        getDefaultRouteForRole(envelope.user.role);

      navigate(destination, { replace: true });
    } catch (submissionError) {
      setError(getErrorMessage(submissionError));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Form
      actions={
        <>
          <Button fullWidth isLoading={isSubmitting} type="submit">
            Sign in
          </Button>
          <p className="form-card__footer">
            New to RideSphere? <Link to="/register/rider">Create rider account</Link> or{" "}
            <Link to="/register/driver">register as driver</Link>.
          </p>
        </>
      }
      onSubmit={handleSubmit}
      subtitle="Authenticate with your role-based account to access your workspace."
      title="Welcome back"
    >
      <Input label="Email address" onChange={(event) => setEmail(event.target.value)} required type="email" value={email} />
      <Input
        label="Password"
        onChange={(event) => setPassword(event.target.value)}
        required
        type="password"
        value={password}
      />
      {error ? <ErrorDisplay message={error} title="Unable to sign in" /> : null}
    </Form>
  );
}
