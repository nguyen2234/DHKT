import React from "react";
import { ArrowUpRight } from "lucide-react";

export interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: string;
  variant?: "default" | "danger" | "warning" | "success" | "info";
  onClick?: () => void;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  variant = "default",
  onClick
}) => {
  const borderHighlight = {
    default: "hover:border-foreground/30",
    danger: "border-l-4 border-l-danger hover:border-danger/60",
    warning: "border-l-4 border-l-warning hover:border-warning/60",
    success: "border-l-4 border-l-success hover:border-success/60",
    info: "border-l-4 border-l-info hover:border-info/60"
  };

  const valueColors = {
    default: "text-foreground",
    danger: "text-danger",
    warning: "text-warning",
    success: "text-success",
    info: "text-info"
  };

  return (
    <div
      onClick={onClick}
      className={`bg-surface border border-border rounded-xl p-5 transition-all ${borderHighlight[variant]} ${
        onClick ? "cursor-pointer hover:shadow-sm" : ""
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <span className="text-xs font-medium text-muted uppercase tracking-wider">{title}</span>
        {icon && <span className="p-2 rounded-lg bg-item-hover text-muted shrink-0">{icon}</span>}
      </div>

      <div className="mt-3 flex items-baseline justify-between">
        <div className={`text-2xl font-bold tracking-tight ${valueColors[variant]}`}>{value}</div>
        {onClick && (
          <ArrowUpRight className="w-4 h-4 text-muted group-hover:text-foreground transition-colors" />
        )}
      </div>

      {(subtitle || trend) && (
        <div className="mt-2 text-xs text-muted flex items-center justify-between">
          <span>{subtitle}</span>
          {trend && <span className="font-medium text-foreground">{trend}</span>}
        </div>
      )}
    </div>
  );
};
