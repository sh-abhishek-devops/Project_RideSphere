import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { getErrorMessage } from "api/client";
import { Button } from "components/Button";
import { ErrorDisplay } from "components/ErrorDisplay";
import { Form } from "components/Form";
import { Input } from "components/Input";
import { useAuth } from "hooks/useAuth";

const initialForm = {
  email: "",
  password: "",
  first_name: "",
  last_name: "",
  phone_number: "",
  is_active: true
};

export function DriverRegistrationPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError("");

    try {
      await auth.registerDriverAccount({ user: form });
      await auth.login({ email: form.email, password: form.password });
      navigate("/driver/dashboard", { replace: true });
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
            Create driver account
          </Button>
          <p className="form-card__footer">
            Already registered? <Link to="/login">Sign in</Link>.
          </p>
        </>
      }
      onSubmit={handleSubmit}
      subtitle="Register a driver profile to manage availability and trip execution."
      title="Driver registration"
    >
      <Input label="First name" onChange={(event) => setForm({ ...form, first_name: event.target.value })} required value={form.first_name} />
      <Input label="Last name" onChange={(event) => setForm({ ...form, last_name: event.target.value })} required value={form.last_name} />
      <Input label="Email address" onChange={(event) => setForm({ ...form, email: event.target.value })} required type="email" value={form.email} />
      <Input label="Phone number" onChange={(event) => setForm({ ...form, phone_number: event.target.value })} required value={form.phone_number} />
      <Input
        label="Password"
        onChange={(event) => setForm({ ...form, password: event.target.value })}
        required
        type="password"
        value={form.password}
      />
      {error ? <ErrorDisplay message={error} title="Registration failed" /> : null}
    </Form>
  );
}
