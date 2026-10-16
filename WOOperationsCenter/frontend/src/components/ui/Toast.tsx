import React from "react";
import { useAppStore, ToastMessage } from "../../stores/appStore";
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from "lucide-react";

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useAppStore();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 max-w-sm pointer-events-none">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={() => removeToast(toast.id)} />
      ))}
    </div>
  );
};

const ToastItem: React.FC<{ toast: ToastMessage; onDismiss: () => void }> = ({ toast, onDismiss }) => {
  const icons = {
    success: <CheckCircle2 className="w-5 h-5 text-success shrink-0" />,
    error: <AlertCircle className="w-5 h-5 text-danger shrink-0" />,
    warning: <AlertTriangle className="w-5 h-5 text-warning shrink-0" />,
    info: <Info className="w-5 h-5 text-info shrink-0" />
  };

  const borders = {
    success: "border-success/30",
    error: "border-danger/30",
    warning: "border-warning/30",
    info: "border-info/30"
  };

  return (
    <div
      className={`pointer-events-auto bg-surface border ${borders[toast.type]} shadow-lg rounded-xl p-3.5 flex items-start gap-3 transition-all animate-in fade-in slide-in-from-bottom-2 duration-200`}
    >
      {icons[toast.type]}
      <div className="flex-1 min-w-0">
        {toast.title && <div className="text-sm font-semibold text-foreground mb-0.5">{toast.title}</div>}
        <div className="text-xs text-muted leading-relaxed">{toast.message}</div>
      </div>
      <button
        onClick={onDismiss}
        className="text-muted hover:text-foreground p-1 rounded-md hover:bg-item-hover transition-colors"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};
