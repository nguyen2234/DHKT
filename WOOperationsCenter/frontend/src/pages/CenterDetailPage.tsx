import React, { useState, useEffect } from "react";
import { useAppStore } from "../stores/appStore";
import { bridge, EmployeeData, WorkOrderItem } from "../services/bridge";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import {
  Building2,
  Users,
  Copy,
  Download,
  AlertTriangle,
  Clock,
  ArrowLeft,
  Check,
  Tag,
  CheckSquare,
  Square,
  FileText
} from "lucide-react";

export const CenterDetailPage: React.FC = () => {
  const { dataset, selectedCenterCode, setCurrentRoute, addToast } = useAppStore();

  const [activeTab, setActiveTab] = useState<"ft" | "overdue" | "pending">("ft");
  const [centerData, setCenterData] = useState<any>(null);
  const [employees, setEmployees] = useState<EmployeeData[]>([]);
  const [notification, setNotification] = useState<string>("");
  const [overdueWos, setOverdueWos] = useState<WorkOrderItem[]>([]);
  const [pendingWos, setPendingWos] = useState<WorkOrderItem[]>([]);
  const [copiedAction, setCopiedAction] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState<boolean>(false);

  const centerCode = selectedCenterCode || (dataset?.centers[0]?.code ?? "");

  useEffect(() => {
    if (centerCode) {
      loadCenterInfo();
    }
  }, [centerCode, dataset]);

  const loadCenterInfo = async () => {
    try {
      const details = await bridge.getCenterDetails(centerCode);
      setCenterData(details);
      setEmployees(details.employees || []);
      setNotification(details.notification || "");

      // Load WOs for this center
      const overdueRes = await bridge.queryWorkOrders({
        center_code: centerCode,
        classification: "overdue",
        page_size: 200
      });
      setOverdueWos(overdueRes.items);

      const pendingRes = await bridge.queryWorkOrders({
        center_code: centerCode,
        classification: "pending",
        page_size: 200
      });
      setPendingWos(pendingRes.items);
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi tải thông tin huyện", message: err.message });
    }
  };

  const handleToggleTag = async (emp: EmployeeData) => {
    const nextState = !emp.is_tagged;
    try {
      await bridge.setEmployeeTag(emp.center_code, emp.username, nextState);
      setEmployees((prev) =>
        prev.map((e) =>
          e.username === emp.username ? { ...e, is_tagged: nextState, is_manually_tagged: nextState } : e
        )
      );
      loadCenterInfo();
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi TAG", message: err.message });
    }
  };

  const handleCopy = async (type: string) => {
    try {
      if (type === "report") {
        await bridge.copyToClipboard("center_report", {
          center_code: centerCode,
          notification
        });
      } else if (type === "notif") {
        await bridge.copyToClipboard("center_notification", { notification });
      } else if (type === "overdue_wo") {
        await bridge.copyToClipboard("center_overdue_wos", { center_code: centerCode });
      } else if (type === "pending_wo") {
        await bridge.copyToClipboard("center_pending_wos", { center_code: centerCode });
      }
      setCopiedAction(type);
      addToast({ type: "success", message: "Đã copy nội dung vào Clipboard" });
      setTimeout(() => setCopiedAction(null), 2500);
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi copy", message: err.message });
    }
  };

  const handleExportSingleExcel = async () => {
    setIsExporting(true);
    try {
      const res = await bridge.exportReport("thft_excel", {
        selected_centers: [centerCode],
        separate_files: true
      });
      if (res.success) {
        addToast({
          type: "success",
          title: "Xuất Excel thành công",
          message: `File báo cáo huyện đã được tạo.`
        });
      }
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi xuất file", message: err.message });
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportWord = async () => {
    try {
      const res = await bridge.exportReport("center_docx", {
        center_code: centerCode,
        notification
      });
      if (res.success) {
        addToast({
          type: "success",
          title: "Xuất Word thành công",
          message: `Đã xuất file Word tại: ${res.output_path}`
        });
      }
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi xuất Word", message: err.message });
    }
  };

  const centerMeta = dataset?.centers.find((c) => c.code === centerCode);
  const taggedCount = employees.filter((e) => e.is_tagged).length;

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentRoute("centers")}
            icon={<ArrowLeft className="w-4 h-4" />}
          >
            Danh sách huyện
          </Button>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <span>Trung tâm {centerMeta?.name || centerCode}</span>
              <Badge variant="primary" size="md">{centerCode}</Badge>
            </h1>
            <p className="text-xs text-muted truncate max-w-md">{centerMeta?.full_name}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <Button
            size="sm"
            onClick={() => handleCopy("report")}
            icon={copiedAction === "report" ? <Check className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
          >
            {copiedAction === "report" ? "Đã copy HTML" : "Copy Báo cáo Huyện"}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleExportSingleExcel}
            isLoading={isExporting}
            icon={<Download className="w-4 h-4" />}
          >
            Xuất Excel
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleExportWord}
            icon={<FileText className="w-4 h-4" />}
          >
            Xuất Word
          </Button>
        </div>
      </div>

      {/* KPI Stats Bar for this Center */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs">
        <div className="bg-surface border border-border p-3.5 rounded-xl">
          <span className="text-muted block text-[11px]">Tổng tồn WO:</span>
          <span className="text-lg font-bold text-foreground mt-0.5 block">{centerMeta?.tong_ton}</span>
        </div>
        <div className="bg-surface border border-border p-3.5 rounded-xl">
          <span className="text-danger block text-[11px]">Tồn quá hạn:</span>
          <span className="text-lg font-bold text-danger mt-0.5 block">{centerMeta?.ton_qua_han}</span>
        </div>
        <div className="bg-surface border border-border p-3.5 rounded-xl">
          <span className="text-success block text-[11px]">Thực hiện ngày:</span>
          <span className="text-lg font-bold text-success mt-0.5 block">{centerMeta?.thuc_hien_ngay}</span>
        </div>
        <div className="bg-surface border border-border p-3.5 rounded-xl">
          <span className="text-muted block text-[11px]">Tổng FT:</span>
          <span className="text-lg font-bold text-foreground mt-0.5 block">{employees.length} FT</span>
        </div>
        <div className="bg-surface border border-border p-3.5 rounded-xl">
          <span className="text-danger block text-[11px]">FT cần TAG:</span>
          <span className="text-lg font-bold text-danger mt-0.5 block">{taggedCount} FT</span>
        </div>
      </div>

      {/* Notification Card */}
      <Card
        header={
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2">
              <Tag className="w-4 h-4 text-primary" />
              <h3 className="text-sm font-semibold text-foreground">Nội dung Thông báo & TAG của Huyện</h3>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleCopy("notif")}
              icon={copiedAction === "notif" ? <Check className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
            >
              {copiedAction === "notif" ? "Đã copy" : "Copy thông báo"}
            </Button>
          </div>
        }
      >
        <div className="bg-background p-3.5 rounded-lg border border-border font-mono text-xs text-foreground leading-relaxed select-text">
          {notification}
        </div>
      </Card>

      {/* Workspace Tabs */}
      <div className="border-b border-border flex items-center gap-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab("ft")}
          className={`pb-3 transition-colors cursor-pointer flex items-center gap-2 ${
            activeTab === "ft"
              ? "border-b-2 border-primary text-foreground font-semibold"
              : "text-muted hover:text-foreground"
          }`}
        >
          <Users className="w-4 h-4" />
          <span>Nhân viên FT ({employees.length})</span>
          {taggedCount > 0 && <Badge variant="danger" size="sm">{taggedCount}</Badge>}
        </button>

        <button
          onClick={() => setActiveTab("overdue")}
          className={`pb-3 transition-colors cursor-pointer flex items-center gap-2 ${
            activeTab === "overdue"
              ? "border-b-2 border-primary text-foreground font-semibold"
              : "text-muted hover:text-foreground"
          }`}
        >
          <AlertTriangle className="w-4 h-4 text-danger" />
          <span>WO Quá hạn ({overdueWos.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("pending")}
          className={`pb-3 transition-colors cursor-pointer flex items-center gap-2 ${
            activeTab === "pending"
              ? "border-b-2 border-primary text-foreground font-semibold"
              : "text-muted hover:text-foreground"
          }`}
        >
          <Clock className="w-4 h-4 text-success" />
          <span>WO Tồn trong hạn ({pendingWos.length})</span>
        </button>
      </div>

      {/* Tab 1: Employee FT Table */}
      {activeTab === "ft" && (
        <Card noPadding>
          <div className="overflow-x-auto max-h-[500px]">
            <table className="w-full text-xs text-left border-collapse select-text">
              <thead className="bg-background border-b border-border text-muted font-semibold sticky top-0 uppercase text-[11px]">
                <tr>
                  <th className="py-2.5 px-3 text-center">TAG</th>
                  <th className="py-2.5 px-3">Tài khoản (FT)</th>
                  <th className="py-2.5 px-3">Họ và tên</th>
                  <th className="py-2.5 px-3">Vị trí</th>
                  <th className="py-2.5 px-3 text-right">Tổng Tồn</th>
                  <th className="py-2.5 px-3 text-right">Quá hạn</th>
                  <th className="py-2.5 px-3 text-right">QH &gt;30N</th>
                  <th className="py-2.5 px-3 text-right">TH Ngày</th>
                  <th className="py-2.5 px-3 text-center">Trạng thái TAG</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {employees.map((emp) => (
                  <tr
                    key={emp.username}
                    className={`hover:bg-item-hover transition-colors ${
                      emp.is_tagged ? "bg-danger-bg/20" : ""
                    }`}
                  >
                    <td className="py-2 px-3 text-center">
                      <button
                        onClick={() => handleToggleTag(emp)}
                        title="Bật/Tắt TAG"
                        className="cursor-pointer text-muted hover:text-foreground p-1"
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
                      {emp.thuc_hien_ngay > 0 ? emp.thuc_hien_ngay : <span className="text-danger">0</span>}
                    </td>
                    <td className="py-2 px-3 text-center">
                      {emp.is_tagged ? (
                        <Badge variant="danger" size="sm">
                          {emp.is_manually_tagged !== null ? "Thủ công" : "Tự động"}
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
      )}

      {/* Tab 2: Overdue WO Table */}
      {activeTab === "overdue" && (
        <Card
          header={
            <div className="flex items-center justify-between w-full">
              <h3 className="text-sm font-semibold text-danger">Danh sách WO Quá hạn ({overdueWos.length} WO)</h3>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleCopy("overdue_wo")}
                icon={<Copy className="w-3.5 h-3.5" />}
              >
                Copy WO Quá hạn (HTML/TSV)
              </Button>
            </div>
          }
          noPadding
        >
          <div className="overflow-x-auto max-h-[500px]">
            <table className="w-full text-xs text-left border-collapse select-text">
              <thead className="bg-[#1F4E78] text-white font-semibold sticky top-0 uppercase text-[11px]">
                <tr>
                  <th className="py-2.5 px-3">STT</th>
                  <th className="py-2.5 px-3">Mã WO</th>
                  <th className="py-2.5 px-3">Loại công việc</th>
                  <th className="py-2.5 px-3">Nội dung</th>
                  <th className="py-2.5 px-3">Hạn kết thúc</th>
                  <th className="py-2.5 px-3">Trạng thái</th>
                  <th className="py-2.5 px-3">Nhân viên</th>
                  <th className="py-2.5 px-3">Mã trạm</th>
                  <th className="py-2.5 px-3 text-center">Số ngày quá hạn</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {overdueWos.map((w, idx) => (
                  <tr key={w.code + idx} className="hover:bg-item-hover transition-colors">
                    <td className="py-2 px-3 text-muted">{idx + 1}</td>
                    <td className="py-2 px-3 font-mono font-medium text-foreground">{w.code}</td>
                    <td className="py-2 px-3 text-muted">{w.job_type}</td>
                    <td className="py-2 px-3 max-w-xs truncate text-foreground" title={w.content}>
                      {w.content}
                    </td>
                    <td className="py-2 px-3 text-muted">{w.deadline}</td>
                    <td className="py-2 px-3">{w.status}</td>
                    <td className="py-2 px-3 font-medium text-foreground">{w.performer}</td>
                    <td className="py-2 px-3 font-mono text-muted">{w.station_code}</td>
                    <td className="py-2 px-3 text-center font-bold text-danger">{w.overdue_days} ngày</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Tab 3: Pending WO Table */}
      {activeTab === "pending" && (
        <Card
          header={
            <div className="flex items-center justify-between w-full">
              <h3 className="text-sm font-semibold text-success">Danh sách WO Tồn trong hạn ({pendingWos.length} WO)</h3>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleCopy("pending_wo")}
                icon={<Copy className="w-3.5 h-3.5" />}
              >
                Copy WO Trong hạn (HTML/TSV)
              </Button>
            </div>
          }
          noPadding
        >
          <div className="overflow-x-auto max-h-[500px]">
            <table className="w-full text-xs text-left border-collapse select-text">
              <thead className="bg-[#135E48] text-white font-semibold sticky top-0 uppercase text-[11px]">
                <tr>
                  <th className="py-2.5 px-3">STT</th>
                  <th className="py-2.5 px-3">Mã WO</th>
                  <th className="py-2.5 px-3">Loại công việc</th>
                  <th className="py-2.5 px-3">Nội dung</th>
                  <th className="py-2.5 px-3">Hạn kết thúc</th>
                  <th className="py-2.5 px-3">Trạng thái</th>
                  <th className="py-2.5 px-3">Nhân viên</th>
                  <th className="py-2.5 px-3">Mã trạm</th>
                  <th className="py-2.5 px-3 text-center">Số ngày còn lại</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {pendingWos.map((w, idx) => (
                  <tr key={w.code + idx} className="hover:bg-item-hover transition-colors">
                    <td className="py-2 px-3 text-muted">{idx + 1}</td>
                    <td className="py-2 px-3 font-mono font-medium text-foreground">{w.code}</td>
                    <td className="py-2 px-3 text-muted">{w.job_type}</td>
                    <td className="py-2 px-3 max-w-xs truncate text-foreground" title={w.content}>
                      {w.content}
                    </td>
                    <td className="py-2 px-3 text-muted">{w.deadline}</td>
                    <td className="py-2 px-3">{w.status}</td>
                    <td className="py-2 px-3 font-medium text-foreground">{w.performer}</td>
                    <td className="py-2 px-3 font-mono text-muted">{w.station_code}</td>
                    <td className="py-2 px-3 text-center font-bold text-success">+{w.overdue_days} ngày</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};
