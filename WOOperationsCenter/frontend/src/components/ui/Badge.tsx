import React from "react";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "success" | "danger" | "warning" | "info" | "neutral" | "primary";
  size?: "sm" | "md";
  dot?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = "neutral",
  size = "md",
  dot = false,
  className = "",
  ...props
}) => {
  const sizeClasses = {
    sm: "text-[11px] px-1.5 py-0.5",
    md: "text-xs px-2 py-0.5"
  };

  const variantClasses = {
    success: "bg-success-bg text-success border border-success/20",
    danger: "bg-danger-bg text-danger border border-danger/20",
    warning: "bg-warning-bg text-warning border border-warning/20",
    info: "bg-info-bg text-info border border-info/20",
    neutral: "bg-neutral-bg text-neutral border border-neutral/20",
    primary: "bg-primary text-primary-foreground"
  };

  const dotColor = {
    success: "bg-success",
    danger: "bg-danger",
    warning: "bg-warning",
    info: "bg-info",
    neutral: "bg-neutral",
    primary: "bg-primary-foreground"
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-md select-none shrink-0 ${sizeClasses[size]} ${variantClasses[variant]} ${className}`}
      {...props}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full ${dotColor[variant]}`} />}
      {children}
    </span>
  );
};
