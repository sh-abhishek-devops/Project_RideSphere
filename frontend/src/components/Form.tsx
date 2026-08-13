import type { FormHTMLAttributes, ReactNode } from "react";

interface FormProps extends FormHTMLAttributes<HTMLFormElement> {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
}

export function Form({ actions, children, subtitle, title, ...props }: FormProps) {
  return (
    <form className="form-card" {...props}>
      <div className="form-card__header">
        <h1>{title}</h1>
        {subtitle ? <p>{subtitle}</p> : null}
      </div>
      <div className="form-card__content">{children}</div>
      {actions ? <div className="form-card__actions">{actions}</div> : null}
    </form>
  );
}
