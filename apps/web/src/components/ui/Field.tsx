import clsx from "clsx";
import type { ComponentProps, ReactNode } from "react";

export const controlClass =
  "min-h-11 w-full rounded-lg border border-line bg-surface px-3 py-2 text-base text-fg transition-colors duration-150 placeholder:text-subtle hover:border-accent focus-visible:border-accent";

/** Rótulo, dica e erro ligados ao controle por id (o controle recebe aria-describedby). */
export function Field({
  id,
  label,
  hint,
  error,
  children,
  className,
}: {
  id: string;
  label: string;
  hint?: string;
  error?: string | null;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={clsx("flex flex-col gap-1.5", className)}>
      <label htmlFor={id} className="text-base font-bold">
        {label}
      </label>
      {children}
      {hint && (
        <p id={`${id}-hint`} className="text-sm text-muted">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} role="alert" className="text-sm font-bold text-loss">
          {error}
        </p>
      )}
    </div>
  );
}

export function describedBy(id: string, hint?: string, error?: string | null) {
  const ids = [hint ? `${id}-hint` : "", error ? `${id}-error` : ""].filter(Boolean).join(" ");
  return ids || undefined;
}

export function TextField({
  id,
  label,
  hint,
  error,
  className,
  ...props
}: Omit<ComponentProps<"input">, "id"> & { id: string; label: string; hint?: string; error?: string | null }) {
  return (
    <Field id={id} label={label} hint={hint} error={error} className={className}>
      <input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(id, hint, error)}
        className={controlClass}
        {...props}
      />
    </Field>
  );
}

export function SelectField({
  id,
  label,
  hint,
  error,
  className,
  children,
  ...props
}: Omit<ComponentProps<"select">, "id"> & { id: string; label: string; hint?: string; error?: string | null }) {
  return (
    <Field id={id} label={label} hint={hint} error={error} className={className}>
      <select
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(id, hint, error)}
        className={controlClass}
        {...props}
      >
        {children}
      </select>
    </Field>
  );
}

export function CheckboxField({
  id,
  label,
  className,
  ...props
}: Omit<ComponentProps<"input">, "id" | "type"> & { id: string; label: ReactNode }) {
  return (
    <div className={clsx("flex items-start gap-3", className)}>
      <input id={id} type="checkbox" className="mt-1 size-6 shrink-0" {...props} />
      <label htmlFor={id} className="text-base">
        {label}
      </label>
    </div>
  );
}
