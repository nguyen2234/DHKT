import React from "react";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  header?: React.ReactNode;
  footer?: React.ReactNode;
  noPadding?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  header,
  footer,
  noPadding = false,
  className = "",
  ...props
}) => {
  return (
    <div
      className={`bg-surface border border-border rounded-xl transition-colors ${className}`}
      {...props}
    >
      {header && (
        <div className="px-5 py-4 border-b border-border flex items-center justify-between gap-4">
          {header}
        </div>
      )}
      <div className={noPadding ? "" : "p-5"}>{children}</div>
      {footer && (
        <div className="px-5 py-3 border-t border-border bg-background/50 rounded-b-xl flex items-center justify-between gap-4">
          {footer}
        </div>
      )}
    </div>
  );
};
