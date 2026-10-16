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

interface NavGroup {
  title: string;
  items: {
    route: AppRoute;
    label: string;
    icon: React.ReactNode;
    badge?: string | number;
  }[];
}

export const Sidebar: React.FC = () => {
  const { currentRoute, setCurrentRoute, sidebarCollapsed, toggleSidebar, dataset } = useAppStore();

  const navGroups: NavGroup[] = [
    {
      title: "NHÓM BÁO CÁO",
      items: [
        {
          route: "dashboard",
          label: "Tổng quan",
          icon: <LayoutDashboard className="w-4 h-4" />
        },
        {
          route: "wo-executive",
          label: "Báo cáo toàn tỉnh",
          icon: <FileText className="w-4 h-4" />
        },
        {
          route: "centers",
          label: "Báo cáo TT huyện",
          icon: <Building2 className="w-4 h-4" />,
          badge: dataset ? dataset.centers.length : undefined
        },
        {
          route: "report-builder",
          label: "Soạn thông báo",
          icon: <Send className="w-4 h-4" />
        },
        {
          route: "batch-report",
          label: "Báo cáo hàng loạt",
          icon: <FileSpreadsheet className="w-4 h-4" />
        }
      ]
    },
    {
      title: "NHÓM DỮ LIỆU",
      items: [
        {
          route: "import",
          label: "Nhập Excel",
          icon: <FileSpreadsheet className="w-4 h-4" />,
          badge: dataset ? "Đã nạp" : undefined
        },
        {
          route: "wo-explorer",
          label: "Danh sách WO",
          icon: <Briefcase className="w-4 h-4" />,
          badge: dataset ? dataset.total_work_orders : undefined
        },
        {
          route: "thft",
          label: "Nhân viên FT",
          icon: <Users className="w-4 h-4" />,
          badge: dataset ? dataset.total_tagged : undefined
        },
        {
          route: "excel-copier",
          label: "Copy bảng Excel",
          icon: <FileText className="w-4 h-4" />
        }
      ]
    },
    {
      title: "HỆ THỐNG",
      items: [
        {
          route: "history",
          label: "Lịch sử báo cáo",
          icon: <History className="w-4 h-4" />
        },
        {
          route: "settings",
          label: "Cài đặt",
          icon: <Settings className="w-4 h-4" />
        }
      ]
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
              <div className="font-bold text-sm text-foreground tracking-tight truncate flex items-center gap-1.5">
                WO Operations
                <span className="text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded font-bold uppercase tracking-wider">Viettel</span>
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
      <nav className="flex-1 p-3 space-y-4 overflow-y-auto">
        {navGroups.map((group, gIdx) => (
          <div key={gIdx} className="space-y-1">
            {!sidebarCollapsed && (
              <div className="px-3 py-1 text-[10px] font-bold text-muted uppercase tracking-wider">
                {group.title}
              </div>
            )}
            {group.items.map((item) => {
              const isActive = currentRoute === item.route;
              return (
                <button
                  key={item.route}
                  onClick={() => setCurrentRoute(item.route)}
                  title={sidebarCollapsed ? item.label : undefined}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                    isActive
                      ? "bg-primary text-primary-foreground shadow-xs font-semibold"
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
          </div>
        ))}
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
