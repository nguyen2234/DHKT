import React from "react";
import { useAppStore, AppRoute } from "../stores/appStore";
import {
  LayoutDashboard,
  FileSpreadsheet,
  FileText,
  Users,
  Briefcase,
  Building2,
  Send,
  History,
  Settings,
  Palette,
  ChevronLeft,
  ChevronRight,
  ShieldCheck
} from "lucide-react";

export const Sidebar: React.FC = () => {
  const { currentRoute, setCurrentRoute, sidebarCollapsed, toggleSidebar, dataset } = useAppStore();

  const navItems: { route: AppRoute; label: string; icon: React.ReactNode; badge?: string | number }[] = [
    {
      route: "dashboard",
      label: "Tổng quan",
      icon: <LayoutDashboard className="w-4 h-4" />
    },
    {
      route: "import",
      label: "Nhập dữ liệu",
      icon: <FileSpreadsheet className="w-4 h-4" />,
      badge: dataset ? "Đã nạp" : undefined
    },
    {
      route: "wo-executive",
      label: "Báo cáo điều hành WO",
      icon: <FileText className="w-4 h-4" />
    },
    {
      route: "thft",
      label: "Báo cáo nhân viên FT",
      icon: <Users className="w-4 h-4" />,
      badge: dataset ? dataset.total_tagged : undefined
    },
    {
      route: "wo-explorer",
      label: "Danh sách công việc WO",
      icon: <Briefcase className="w-4 h-4" />,
      badge: dataset ? dataset.total_work_orders : undefined
    },
    {
      route: "centers",
      label: "Trung tâm huyện",
      icon: <Building2 className="w-4 h-4" />,
      badge: dataset ? dataset.centers.length : undefined
    },
    {
      route: "report-builder",
      label: "Soạn thông báo",
      icon: <Send className="w-4 h-4" />
    },
    {
      route: "history",
      label: "Lịch sử báo cáo",
      icon: <History className="w-4 h-4" />
    },
    {
      route: "settings",
      label: "Cài đặt",
      icon: <Settings className="w-4 h-4" />
    },
    {
      route: "design-system",
      label: "Thư viện thiết kế",
      icon: <Palette className="w-4 h-4" />
    }
  ];

  return (
    <aside
      className={`bg-surface border-r border-border transition-all duration-200 flex flex-col shrink-0 select-none ${
        sidebarCollapsed ? "w-18" : "w-64"
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 px-4 border-b border-border flex items-center justify-between gap-3 shrink-0">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="w-9 h-9 rounded-xl bg-primary flex items-center justify-center text-primary-foreground font-bold shadow-xs shrink-0">
            <ShieldCheck className="w-5 h-5" />
          </div>
          {!sidebarCollapsed && (
            <div className="min-w-0">
              <div className="font-bold text-sm text-foreground tracking-tight truncate">
                WO Operations
              </div>
              <div className="text-[11px] text-muted truncate">Phòng VHKT — NAN_DHKT</div>
            </div>
          )}
        </div>

        <button
          onClick={toggleSidebar}
          title={sidebarCollapsed ? "Mở rộng thanh bên" : "Thu gọn thanh bên"}
          className="p-1.5 text-muted hover:text-foreground hover:bg-item-hover rounded-lg transition-colors cursor-pointer shrink-0"
        >
          {sidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = currentRoute === item.route;
          return (
            <button
              key={item.route}
              onClick={() => setCurrentRoute(item.route)}
              title={sidebarCollapsed ? item.label : undefined}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                isActive
                  ? "bg-primary text-primary-foreground shadow-xs"
                  : "text-muted hover:text-foreground hover:bg-item-hover"
              } ${sidebarCollapsed ? "justify-center" : ""}`}
            >
              <span className="shrink-0">{item.icon}</span>
              {!sidebarCollapsed && (
                <>
                  <span className="truncate flex-1 text-left">{item.label}</span>
                  {item.badge !== undefined && (
                    <span
                      className={`text-[11px] px-1.5 py-0.2 rounded-full font-semibold ${
                        isActive
                          ? "bg-primary-foreground/20 text-primary-foreground"
                          : "bg-secondary text-muted"
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </button>
          );
        })}
      </nav>

      {/* Dataset Status Footer */}
      <div className="p-3 border-t border-border">
        {sidebarCollapsed ? (
          <div
            className={`w-3 h-3 rounded-full mx-auto ${dataset ? "bg-success" : "bg-muted"}`}
            title={dataset ? `Đã nạp: ${dataset.report_date_str}` : "Chưa có dữ liệu"}
          />
        ) : (
          <div className="bg-background rounded-lg p-2.5 text-xs text-muted">
            <div className="flex items-center gap-2 mb-1">
              <span className={`w-2 h-2 rounded-full shrink-0 ${dataset ? "bg-success" : "bg-muted"}`} />
              <span className="font-semibold text-foreground truncate">
                {dataset ? "Dữ liệu đang hoạt động" : "Chưa nạp tệp"}
              </span>
            </div>
            {dataset ? (
              <div className="text-[11px] text-muted truncate">
                Ngày: <span className="font-medium text-foreground">{dataset.report_date_str}</span> (
                {dataset.centers.length} TT)
              </div>
            ) : (
              <div className="text-[11px]">Vui lòng vào tab Nhập dữ liệu</div>
            )}
          </div>
        )}
      </div>
    </aside>
  );
};
