import React, { useState, useEffect } from "react";
import { useAppStore } from "../stores/appStore";
import { bridge, EmployeeData } from "../services/bridge";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { ExportModal } from "../components/modals/ExportModal";
import { CopyModeModal } from "../components/modals/CopyModeModal";
import { copyFormattedTable, ClipboardCopyMode } from "../services/clipboardHelper";
import {
  Users,
  Copy,
  Download,
  Filter,
  Check,
  Tag,
  Building,
  CheckSquare,
  Square,
  Search,
  ExternalLink
} from "lucide-react";

export const THFTPage: React.FC = () => {
  const { dataset, positionFilter, setPositionFilter, addToast, setCurrentRoute } = useAppStore();

  const [selectedCenter, setSelectedCenter] = useState<string>("");
  const [employees, setEmployees] = useState<EmployeeData[]>([]);
  const [notification, setNotification] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [tagFormat, setTagFormat] = useState<string>("name");
  const [isExportModalOpen, setIsExportModalOpen] = useState<boolean>(false);
  const [isCopyModalOpen, setIsCopyModalOpen] = useState<boolean>(false);
  const [copiedType, setCopiedType] = useState<string | null>(null);

  useEffect(() => {
    if (dataset && dataset.centers.length > 0) {
      if (!selectedCenter || !dataset.centers.find((c) => c.code === selectedCenter)) {
        setSelectedCenter(dataset.centers[0].code);
      }
    }
  }, [dataset]);

  useEffect(() => {
    if (dataset && selectedCenter) {
      loadCenterData(selectedCenter);
    }
  }, [dataset, selectedCenter, positionFilter, tagFormat]);

  const loadCenterData = async (centerCode: string) => {
    try {
      const res = await bridge.getCenterDetails(centerCode);
      if (res && res.employees) {
        setEmployees(res.employees);
        setNotification(res.notification);
      }
    } catch (err: any) {
      console.error("Failed to load center details:", err);
    }
  };

  const handleToggleTag = async (emp: EmployeeData) => {
    const nextState = !emp.is_tagged;
    try {
      await bridge.setEmployeeTag(emp.center_code, emp.username, nextState);
      // Update local state
      setEmployees((prev) =>
        prev.map((e) =>
          e.username === emp.username ? { ...e, is_tagged: nextState, is_manually_tagged: nextState } : e
        )
      );
      // Reload notification string
      loadCenterData(selectedCenter);
      addToast({
        type: "info",
        message: `${nextState ? "Đã bật" : "Đã tắt"} TAG cho ${emp.full_name} (${emp.username})`
      });
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi cập nhật TAG", message: err.message });
    }
  };

  const handleCopyReport = async () => {
    try {
      const ok = await bridge.copyToClipboard("center_report", {
        center_code: selectedCenter,
        notification
      });
      if (ok) {
        setCopiedType("report");
        addToast({
          type: "success",
          title: "Đã copy báo cáo huyện",
          message: "Đã tạo bảng HTML Table & Text trong Clipboard cho nhóm chat TAMMI."
        });
        setTimeout(() => setCopiedType(null), 2500);
      }
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi copy", message: err.message });
    }
  };

  const handleCopyNotif = async () => {
    try {
      const ok = await bridge.copyToClipboard("center_notification", { notification });
      if (ok) {
        setCopiedType("notif");
        addToast({
          type: "success",
          title: "Đã copy thông báo & TAG",
          message: "Đã copy nội dung thông báo kèm danh sách tag vào Clipboard."
        });
        setTimeout(() => setCopiedType(null), 2500);
      }
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi copy", message: err.message });
    }
  };

  if (!dataset) {
    return (
      <div className="py-16 text-center max-w-md mx-auto">
        <Users className="w-12 h-12 text-muted mx-auto mb-3" />
        <h3 className="text-base font-semibold text-foreground">Chưa có dữ liệu</h3>
        <p className="text-xs text-muted mt-1">Vui lòng nạp tệp Excel điều hành trước.</p>
        <div className="mt-4">
          <Button onClick={() => setCurrentRoute("import")}>Đến trang Nhập dữ liệu</Button>
        </div>
      </div>
    );
  }

  // Filter employees by position and search query
  const filteredEmployees = employees.filter((emp) => {
    // Position filter
    if (positionFilter === "NV DM") {
      if (!emp.position.toUpperCase().includes("DM")) return false;
    } else if (positionFilter === "NV NHÀ TRẠM") {
      if (!emp.position.toUpperCase().includes("TRẠM") && !emp.position.toUpperCase().includes("TRAM")) return false;
    }

    // Search query
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        emp.username.toLowerCase().includes(q) ||
        emp.full_name.toLowerCase().includes(q) ||
        emp.position.toLowerCase().includes(q)
      );
    }

    return true;
  });

  const taggedCount = filteredEmployees.filter((e) => e.is_tagged).length;

  return (
    <div className="space-y-6">
      {/* Header & Main Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Báo cáo Nhân viên Kỹ thuật FT (Module B)
          </h1>
          <p className="text-xs text-muted mt-1">
            Quy tắc TAG chuẩn: <span className="font-semibold text-danger">TỒN &gt; 0 VÀ THỰC HIỆN NGÀY &le; 0</span> (Độc lập từng huyện)
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          <Button
            size="sm"
            onClick={handleCopyReport}
            icon={copiedType === "report" ? <Check className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
          >
            {copiedType === "report" ? "Đã copy bảng HTML" : "Copy Báo cáo Huyện"}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleCopyNotif}
            icon={copiedType === "notif" ? <Check className="w-4 h-4 text-success" /> : <Tag className="w-4 h-4 text-primary" />}
          >
            Copy Thông báo + TAG
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsExportModalOpen(true)}
            icon={<Download className="w-4 h-4 text-primary" />}
          >
            Xuất Excel Huyện
          </Button>
        </div>
      </div>

      {/* Control Bar: Center Selector, Position Filters, Tag Formats */}
      <div className="bg-surface border border-border rounded-xl p-4 flex flex-col lg:flex-row lg:items-center justify-between gap-4 text-xs">
        {/* Center Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 lg:pb-0 scrollbar-clean">
          <span className="font-medium text-muted shrink-0 mr-1 flex items-center gap-1">
            <Building className="w-3.5 h-3.5" /> Huyện:
          </span>
          {dataset.centers.map((c) => (
            <button
              key={c.code}
              onClick={() => setSelectedCenter(c.code)}
              className={`px-3 py-1.5 rounded-lg font-semibold shrink-0 transition-colors cursor-pointer ${
                selectedCenter === c.code
                  ? "bg-primary text-primary-foreground shadow-xs"
                  : "bg-background text-muted hover:text-foreground hover:bg-item-hover"
              }`}
            >
              {c.code} ({c.name})
            </button>
          ))}
        </div>

        {/* Position Filter Buttons */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="flex items-center gap-1 bg-background p-1 rounded-lg border border-border">
            {["Tất cả", "NV DM", "NV NHÀ TRẠM"].map((pos) => (
              <button
                key={pos}
                onClick={() => setPositionFilter(pos)}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors cursor-pointer ${
                  positionFilter === pos
                    ? "bg-surface text-foreground font-semibold shadow-xs"
                    : "text-muted hover:text-foreground"
                }`}
              >
                {pos}
              </button>
            ))}
          </div>

          {/* Tag Token Format Selector */}
          <select
            value={tagFormat}
            onChange={(e) => setTagFormat(e.target.value)}
            className="bg-background border border-border-strong rounded-lg px-2.5 py-1.5 text-foreground focus:outline-none"
          >
            <option value="name">@Họ và tên</option>
            <option value="name_upper">@HỌ VÀ TÊN</option>
            <option value="username">@username</option>
            <option value="ft_username">@FT username</option>
            <option value="user_pos_center">@username VịTrí Huyện</option>
          </select>
        </div>
      </div>

      {/* Notification & Tag Preview Card */}
      <Card
        header={
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2">
              <Tag className="w-4 h-4 text-primary" />
              <h3 className="text-sm font-semibold text-foreground">
                Thông báo & Danh sách TAG nhân viên ({taggedCount} nhân viên cần TAG)
              </h3>
            </div>
            <div className="text-xs text-muted">
              Độc lập cho Trung tâm <span className="font-bold text-foreground">{selectedCenter}</span>
            </div>
          </div>
        }
      >
        <div className="bg-background p-3.5 rounded-lg border border-border font-mono text-xs text-foreground leading-relaxed">
          {notification || "Đang tải thông báo..."}
        </div>
      </Card>

      {/* Employee Table */}
      <Card
        header={
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 w-full">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-foreground">
                Danh sách Nhân sự FT — {selectedCenter}
              </h3>
              <Badge variant="neutral" size="sm">
                {filteredEmployees.length} nhân viên
              </Badge>
              <Badge variant="danger" size="sm">
                {taggedCount} cần TAG
              </Badge>
            </div>

            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-muted absolute left-2.5 top-2.5" />
                <input
                  type="text"
                  placeholder="Lọc nhân viên..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="bg-background border border-border-strong rounded-lg pl-8 pr-3 py-1.5 text-xs text-foreground focus:outline-none w-44"
                />
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentRoute("center-detail", selectedCenter)}
                icon={<ExternalLink className="w-3.5 h-3.5" />}
              >
                Không gian huyện
              </Button>
            </div>
          </div>
        }
        noPadding
      >
        <div className="overflow-x-auto max-h-[500px]">
          <table className="w-full text-xs text-left border-collapse select-text">
            <thead className="bg-background border-b border-border text-muted font-semibold sticky top-0 z-10 uppercase text-[11px]">
              <tr>
                <th className="py-2.5 px-3 text-center">TAG</th>
                <th className="py-2.5 px-3">Tài khoản (FT)</th>
                <th className="py-2.5 px-3">Họ và tên</th>
                <th className="py-2.5 px-3">Vị trí</th>
                <th className="py-2.5 px-3 text-right">Tổng Tồn (Q)</th>
                <th className="py-2.5 px-3 text-right">Quá hạn (R)</th>
                <th className="py-2.5 px-3 text-right">QH &gt;30N (S)</th>
                <th className="py-2.5 px-3 text-right">TH Ngày (T)</th>
                <th className="py-2.5 px-3 text-center">Trạng thái TAG</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredEmployees.map((emp) => (
                <tr
                  key={emp.username}
                  className={`hover:bg-item-hover transition-colors ${
                    emp.is_tagged ? "bg-danger-bg/20" : ""
                  }`}
                >
                  <td className="py-2 px-3 text-center">
                    <button
                      onClick={() => handleToggleTag(emp)}
                      title="Bật/Tắt TAG thủ công"
                      className="cursor-pointer text-muted hover:text-foreground p-1 rounded"
                    >
                      {emp.is_tagged ? (
                        <CheckSquare className="w-4 h-4 text-danger" />
                      ) : (
                        <Square className="w-4 h-4 text-muted" />
                      )}
                    </button>
                  </td>
                  <td className="py-2 px-3 font-mono font-medium text-foreground">{emp.username}</td>
                  <td className="py-2 px-3 font-medium text-foreground">{emp.full_name}</td>
                  <td className="py-2 px-3 text-muted">{emp.position}</td>
                  <td className="py-2 px-3 text-right font-bold text-foreground">
                    {emp.ton > 0 ? emp.ton : "—"}
                  </td>
                  <td className="py-2 px-3 text-right font-semibold text-danger">
                    {emp.qua_han > 0 ? emp.qua_han : "—"}
                  </td>
                  <td className="py-2 px-3 text-right font-medium text-warning">
                    {emp.qua_han_30 > 0 ? emp.qua_han_30 : "—"}
                  </td>
                  <td className="py-2 px-3 text-right font-bold text-success">
                    {emp.thuc_hien_ngay > 0 ? (
                      emp.thuc_hien_ngay
                    ) : (
                      <span className="text-danger font-semibold">0</span>
                    )}
                  </td>
                  <td className="py-2 px-3 text-center">
                    {emp.is_tagged ? (
                      <Badge variant="danger" size="sm">
                        {emp.is_manually_tagged !== null ? "TAG (Thủ công)" : "TAG (Tự động)"}
                      </Badge>
                    ) : (
                      <span className="text-[11px] text-muted">Không tag</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <ExportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        reportType="thft_excel"
        centerCode={selectedCenter}
        positionFilter={positionFilter}
      />
    </div>
  );
};
