import React from "react";
import { useAppStore } from "../stores/appStore";
import { Badge } from "../components/ui/Badge";
import {
  Calendar,
  FileCheck2,
  FileX2,
  Search,
  Sun,
  Moon,
  Settings,
  HelpCircle
} from "lucide-react";

export const TopBar: React.FC = () => {
  const { dataset, theme, toggleTheme, setCurrentRoute } = useAppStore();

  return (
    <header className="h-16 px-6 border-b border-border bg-surface flex items-center justify-between gap-4 shrink-0 select-none">
      {/* Left section: Status & Report Date */}
      <div className="flex items-center gap-4">
        {dataset ? (
          <div className="flex items-center gap-2.5">
            <Badge variant="success" dot size="md">
              <span className="flex items-center gap-1.5 font-medium">
                <FileCheck2 className="w-3.5 h-3.5" />
                <span>Đã nạp workbook</span>
              </span>
            </Badge>

            <div className="h-4 w-px bg-border mx-1" />

            <div className="flex items-center gap-1.5 text-xs text-muted">
              <Calendar className="w-3.5 h-3.5" />
              <span>Ngày báo cáo:</span>
              <span className="font-semibold text-foreground">{dataset.report_date_str}</span>
            </div>

            {dataset.province_summary.has_discrepancy && (
              <Badge variant="warning" size="sm">
                Cảnh báo sai lệch số liệu
              </Badge>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <Badge variant="neutral" dot size="md">
              <span className="flex items-center gap-1.5">
                <FileX2 className="w-3.5 h-3.5" />
                <span>Chưa chọn tệp dữ liệu</span>
              </span>
            </Badge>
          </div>
        )}
      </div>

      {/* Right section: Global Search, Theme Switch, Quick Actions */}
      <div className="flex items-center gap-2.5">
        <button
          onClick={() => setCurrentRoute("wo-explorer")}
          className="flex items-center gap-2 px-3 py-1.5 text-xs text-muted bg-background border border-border-strong rounded-lg hover:text-foreground hover:border-foreground/30 transition-colors cursor-pointer"
        >
          <Search className="w-3.5 h-3.5" />
          <span>Tìm kiếm WO, nhân viên, mã trạm...</span>
          <kbd className="text-[10px] bg-surface border border-border px-1.5 py-0.5 rounded text-muted">
            Ctrl+K
          </kbd>
        </button>

        <div className="h-4 w-px bg-border mx-1" />

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          title={theme === "light" ? "Chuyển sang chế độ Tối" : "Chuyển sang chế độ Sáng"}
          className="p-2 text-muted hover:text-foreground hover:bg-item-hover rounded-lg transition-colors cursor-pointer"
        >
          {theme === "light" ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
        </button>

        {/* Settings button */}
        <button
          onClick={() => setCurrentRoute("settings")}
          title="Cài đặt hệ thống"
          className="p-2 text-muted hover:text-foreground hover:bg-item-hover rounded-lg transition-colors cursor-pointer"
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
