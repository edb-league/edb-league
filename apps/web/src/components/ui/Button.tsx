import clsx from "clsx";
import Link from "next/link";
import type { ButtonHTMLAttributes, ComponentProps } from "react";

const base =
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-lg px-4 py-2 text-base font-bold no-underline transition-colors disabled:cursor-not-allowed disabled:opacity-60";

const variants = {
  primary: "bg-accent-bg text-on-accent hover:brightness-110",
  secondary: "border border-line bg-surface-2 text-fg hover:bg-surface-3",
  ghost: "text-accent hover:bg-surface-2",
  danger: "border border-loss bg-surface text-loss hover:bg-surface-2",
} as const;

export type ButtonVariant = keyof typeof variants;

export function Button({
  variant = "primary",
  className,
  type = "button",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }) {
  return <button type={type} className={clsx(base, variants[variant], className)} {...props} />;
}

export function LinkButton({
  variant = "secondary",
  className,
  ...props
}: ComponentProps<typeof Link> & { variant?: ButtonVariant }) {
  return <Link className={clsx(base, variants[variant], className)} {...props} />;
}
