import React, { useState, useEffect } from "react";
import { useAppStore } from "../stores/appStore";
import { bridge } from "../services/bridge";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { KpiCard } from "../components/ui/KpiCard";
import {
  FileText,
  Copy,
  Download,
  RotateCcw,
  Check,
  Send,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Calendar,
  Building
} from "lucide-react";

export const WOExecutivePage: React.FC = () => {
  const { dataset, addToast, setCurrentRoute } = useAppStore();

  const [recipient, setRecipient] = useState("Kính gửi PGĐ @NAN PGĐ A THẮNG , TP @A Sơnpb1 TPKT NAN , TTH!");
  const [deadlineQh, setDeadlineQh] = useState("30/09");
  const [deadlineMonth, setDeadlineMonth] = useState("05/10");
  const [notification, setNotification] = useState("");
  const [reportText, setReportText] = useState("");
  const [isManuallyEdited, setIsManuallyEdited] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (dataset) {
      const thang = dataset.province_summary.month;
      const notifDefault = `Đóng Wo quá hạn trước ${deadlineQh}.\nĐóng hết wo tháng ${thang} xong trước ${deadlineMonth}.`;
      setNotification(notifDefault);
      generateReport(recipient, notifDefault, deadlineQh, deadlineMonth);
    }
  }, [dataset]);

  const generateReport = async (
    recip: string,
    notif: string,
    dlQh: string,
    dlMonth: string
  ) => {
    if (!dataset) return;
    try {
      const text = await bridge.getExecutiveReportText({
        recipient: recip,
        notification: notif,
        deadline_qh: dlQh,
        deadline_month: dlMonth
      });
      setReportText(text);
      setIsManuallyEdited(false);
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi sinh báo cáo", message: err.message });
    }
  };

  const handleCopyReport = async () => {
    try {
      const ok = await bridge.copyToClipboard("text", { text: reportText });
      if (ok) {
        setCopied(true);
        addToast({
          type: "success",
          title: "Đã sao chép",
          message: "Văn bản báo cáo đã được lưu vào Clipboard. Bạn có thể dán trực tiếp (Ctrl+V) vào nhóm chat TAMMI."
        });
        setTimeout(() => setCopied(false), 2500);
      }
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi sao chép", message: err.message });
    }
  };

  const handleExportExcel = async () => {
    if (!dataset) return;
    setIsExporting(true);
    try {
      const res = await bridge.exportReport("executive_excel", {
        preview_text: reportText
      });
      if (res.success && res.output_path) {
        addToast({
          type: "success",
          title: "Xuất file thành công",
          message: `Báo cáo Excel đã được xuất tại: ${res.output_path}`
        });
      } else {
        throw new Error(res.error || "Không thể xuất file");
      }
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi xuất file", message: err.message });
    } finally {
      setIsExporting(false);
    }
  };

  if (!dataset) {
    return (
      <div className="py-16 text-center max-w-md mx-auto">
        <FileText className="w-12 h-12 text-muted mx-auto mb-3" />
        <h3 className="text-base font-semibold text-foreground">Chưa có dữ liệu</h3>
        <p className="text-xs text-muted mt-1">Vui lòng nạp tệp Excel điều hành trước.</p>
        <div className="mt-4">
          <Button onClick={() => setCurrentRoute("import")}>Đến trang Nhập dữ liệu</Button>
        </div>
      </div>
    );
  }

  const ps = dataset.province_summary;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Báo cáo Điều hành WO Toàn tỉnh (Module A)
          </h1>
          <p className="text-xs text-muted mt-1">
            Trích xuất từ sheet <span className="font-semibold text-foreground">TH TTH</span> — Tiến độ cắt tồn WO tháng {ps.month}
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportExcel}
            isLoading={isExporting}
            icon={<Download className="w-4 h-4" />}
          >
            Xuất Excel (BaoCao & ChiTiet)
          </Button>

          <Button
            size="sm"
            onClick={handleCopyReport}
            icon={copied ? <Check className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
          >
            {copied ? "Đã sao chép" : "Sao chép báo cáo"}
          </Button>
        </div>
      </div>

      {/* Discrepancy Warning */}
      {ps.has_discrepancy && (
        <div className="p-4 rounded-xl bg-warning-bg border border-warning/30 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-warning shrink-0 mt-0.5" />
          <div className="text-xs">
            <div className="font-semibold text-warning mb-1">Cảnh báo sai lệch dòng tổng cộng:</div>
            <div className="text-foreground">{ps.discrepancy_details}</div>
          </div>
        </div>
      )}

      {/* 4 Summary Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard
          title="Thực hiện ngày"
          value={`${ps.thuc_hien_ngay} WO`}
          subtitle="Cột T (Dòng tổng cộng)"
          variant="success"
          icon={<CheckCircle2 className="w-4 h-4" />}
        />
        <KpiCard
          title="Tổng tồn WO"
          value={`${ps.tong_ton} WO`}
          subtitle="Cột Q (Dòng tổng cộng)"
          variant="default"
          icon={<FileText className="w-4 h-4" />}
        />
        <KpiCard
          title="Tồn quá hạn"
          value={`${ps.ton_qua_han} WO`}
          subtitle="Cột R (Dòng tổng cộng)"
          variant="danger"
          icon={<AlertTriangle className="w-4 h-4" />}
        />
        <KpiCard
          title="Tồn > 30 ngày"
          value={`${ps.ton_tren_30_ngay} WO`}
          subtitle={ps.overdue_30_centers.map(([c, n]) => `${c}:${n}`).join(", ") || "Không có"}
          variant="warning"
          icon={<Clock className="w-4 h-4" />}
        />
      </div>

      {/* Top 5 Centers Banner */}
      <div className="bg-surface border border-border rounded-xl p-4 flex items-center justify-between flex-wrap gap-3 text-xs">
        <div className="flex items-center gap-2">
          <Building className="w-4 h-4 text-muted" />
          <span className="text-muted">Top 5 Trung tâm tồn cao:</span>
          <span className="font-bold text-foreground tracking-wider">{ps.top_centers.join(", ")}</span>
        </div>
        <div className="text-muted">
          Chi tiết tồn &gt; 30 ngày: <span className="font-semibold text-danger">{ps.overdue_30_centers.map(([c, n]) => `(${c}:${n})`).join(" ") || "0 WO"}</span>
        </div>
      </div>

      {/* Configuration & Live Preview Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Configuration Form (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <Card
            header={
              <div className="flex items-center justify-between w-full">
                <h3 className="text-sm font-semibold text-foreground">Thiết lập Báo cáo & Thông báo</h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => generateReport(recipient, notification, deadlineQh, deadlineMonth)}
                  icon={<RotateCcw className="w-3.5 h-3.5" />}
                  title="Sinh lại nội dung từ dữ liệu"
                >
                  Tạo lại
                </Button>
              </div>
            }
          >
            <div className="space-y-4 text-xs">
              <div>
                <label className="font-medium text-foreground block mb-1.5">Người nhận thông báo:</label>
                <input
                  type="text"
                  value={recipient}
                  onChange={(e) => {
                    setRecipient(e.target.value);
                    if (!isManuallyEdited) generateReport(e.target.value, notification, deadlineQh, deadlineMonth);
                  }}
                  className="w-full bg-background border border-border-strong rounded-lg px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-medium text-foreground block mb-1.5">Hạn chót WO quá hạn:</label>
                  <input
                    type="text"
                    value={deadlineQh}
                    onChange={(e) => {
                      setDeadlineQh(e.target.value);
                      const notif = `Đóng Wo quá hạn trước ${e.target.value}.\nĐóng hết wo tháng ${ps.month} xong trước ${deadlineMonth}.`;
                      setNotification(notif);
                      if (!isManuallyEdited) generateReport(recipient, notif, e.target.value, deadlineMonth);
                    }}
                    placeholder="VD: 30/09"
                    className="w-full bg-background border border-border-strong rounded-lg px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                </div>

                <div>
                  <label className="font-medium text-foreground block mb-1.5">Hạn chót WO tháng:</label>
                  <input
                    type="text"
                    value={deadlineMonth}
                    onChange={(e) => {
                      setDeadlineMonth(e.target.value);
                      const notif = `Đóng Wo quá hạn trước ${deadlineQh}.\nĐóng hết wo tháng ${ps.month} xong trước ${e.target.value}.`;
                      setNotification(notif);
                      if (!isManuallyEdited) generateReport(recipient, notif, deadlineQh, e.target.value);
                    }}
                    placeholder="VD: 05/10"
                    className="w-full bg-background border border-border-strong rounded-lg px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                </div>
              </div>

              <div>
                <label className="font-medium text-foreground block mb-1.5">Nội dung thông báo đề nghị:</label>
                <textarea
                  rows={3}
                  value={notification}
                  onChange={(e) => {
                    setNotification(e.target.value);
                    if (!isManuallyEdited) generateReport(recipient, e.target.value, deadlineQh, deadlineMonth);
                  }}
                  className="w-full bg-background border border-border-strong rounded-lg px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 resize-none font-sans"
                />
              </div>
            </div>
          </Card>
        </div>

        {/* Right: Live Preview & Manual Editor (7 cols) */}
        <div className="lg:col-span-7">
          <Card
            header={
              <div className="flex items-center justify-between w-full">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-foreground">Khung xem trước tin nhắn TAMMI</h3>
                  {isManuallyEdited && (
                    <Badge variant="warning" size="sm">
                      Đã sửa thủ công
                    </Badge>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleCopyReport}
                    icon={copied ? <Check className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
                  >
                    {copied ? "Đã copy" : "Copy"}
                  </Button>
                </div>
              </div>
            }
            noPadding
          >
            <div className="p-4">
              <textarea
                value={reportText}
                onChange={(e) => {
                  setReportText(e.target.value);
                  setIsManuallyEdited(true);
                }}
                rows={16}
                className="w-full bg-background border border-border rounded-lg p-4 font-mono text-xs text-foreground leading-relaxed focus:outline-none focus:ring-2 focus:ring-primary/20 resize-none select-text"
              />
            </div>
            <div className="px-5 py-3 border-t border-border bg-background/50 flex items-center justify-between text-xs text-muted">
              <span>Nội dung chỉnh sửa thủ công sẽ không bị tự động ghi đè khi đổi cài đặt.</span>
              <button
                onClick={() => generateReport(recipient, notification, deadlineQh, deadlineMonth)}
                className="text-primary hover:underline font-medium cursor-pointer"
              >
                Khôi phục bản gốc
              </button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
