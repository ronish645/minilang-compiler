import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "../../lib/cn";

type Variant = "primary" | "secondary" | "ghost";
type Size = "sm" | "md";

const VARIANTS: Record<Variant, string> = {
  primary: "bg-accent text-white hover:brightness-110 shadow-sm",
  secondary: "bg-surface text-ink ring-1 ring-inset ring-border-strong hover:bg-surface-2",
  ghost: "text-ink-2 hover:bg-surface-2 hover:text-ink",
};

const SIZES: Record<Size, string> = {
  sm: "h-8 px-3 text-sm gap-1.5",
  md: "h-10 px-4 text-sm gap-2",
};

export const buttonClasses = (variant: Variant = "secondary", size: Size = "md") =>
  cn(
    "inline-flex select-none items-center justify-center rounded-lg font-medium transition",
    "disabled:pointer-events-none disabled:opacity-50",
    VARIANTS[variant],
    SIZES[size],
  );

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  icon?: ReactNode;
}

export function Button({ variant, size, icon, className, children, ...rest }: ButtonProps) {
  return (
    <button type="button" className={cn(buttonClasses(variant, size), className)} {...rest}>
      {icon}
      {children}
    </button>
  );
}
