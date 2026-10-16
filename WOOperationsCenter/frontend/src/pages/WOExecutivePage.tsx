import React, { useState, useEffect, useRef } from "react";
import { useAppStore } from "../stores/appStore";
import { bridge } from "../services/bridge";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { KpiCard } from "../components/ui/KpiCard";
import { ExportModal } from "../components/modals/ExportModal";
import { CopyModeModal } from "../components/modals/CopyModeModal";
import { copyFormattedTable, ClipboardCopyMode } from "../services/clipboardHelper";
import {
  FileText,
  Copy,
  Download,
  RotateCcw,
  Check,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Calendar,
  Building,
  FolderOpen,
  BookmarkPlus,
  ArrowRight,
  TrendingUp,
  Table as TableIcon
} from "lucide-react";

export const WOExecutivePage: React.FC = () => {
  const { dataset, setDataset, addToast, setCurrentRoute } = useAppStore();

  const [recipient, setRecipient] = useState("Kính gửi PGĐ @NAN PGĐ A THẮNG , TP @A Sơnpb1 TPKT NAN , TTH!");
  const [deadlineQh, setDeadlineQh] = useState("30/09");
  const [deadlineMonth, setDeadlineMonth] = useState("05/10");
  const [notification, setNotification] = useState("");
  const [reportText, setReportText] = useState("");
  const [isManuallyEdited, setIsManuallyEdited] = useState(false);

  // Modals state
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [isCopyTableModalOpen, setIsCopyTableModalOpen] = useState(false);
  const [copiedText, setCopiedText] = useState(false);

  const tableRef = useRef<HTMLDivElement>(null);

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

  const handlePickOtherFile = async () => {
    try {
      const filePath = await bridge.pickExcelFile();
      if (filePath && filePath.trim()) {
        const ds = await bridge.loadExcelDataset(filePath);
        setDataset(ds);
        addToast({
          type: "success",
          title: "Đã nạp file mới",
          message: `Nạp thành công dữ liệu ngày ${ds.report_date_str} (${ds.centers.length} trung tâm).`
        });
      }
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi nạp file", message: err.message });
    }
  };

  const handleCopyReportText = async () => {
    try {
      const ok = await bridge.copyToClipboard("text", { text: reportText });
      if (ok) {
        setCopiedText(true);
        addToast({
          type: "success",
          title: "Đã sao chép nội dung toàn tỉnh",
          message: "Văn bản báo cáo đã sẵn sàng trong Clipboard để dán vào nhóm TAMMI."
        });
        setTimeout(() => setCopiedText(false), 2500);
      }
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi sao chép", message: err.message });
    }
  };

  const handleSaveTemplate = async () => {
    try {
      const templateName = `Mẫu ĐH toàn tỉnh ngày ${dataset?.day_month_str || ""}`;
      await bridge.saveTemplate(templateName, "executive", reportText, "{NGUOI_NHAN}, {THANG}, {NGAY}", false);
      addToast({
        type: "success",
        title: "Đã lưu mẫu thông báo",
        message: `Mẫu "${templateName}" đã được lưu vào hệ thống.`
      });
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi lưu mẫu", message: err.message });
    }
  };

  const buildProvinceTableHtml = () => {
    if (!dataset) return "";
    const rows = dataset.centers.map((c, idx) => `
      <tr style="background-color: ${idx % 2 === 0 ? "#ffffff" : "#f8fafc"};">
        <td style="border: 1px solid #000; text-align: center;">${idx + 1}</td>
        <td style="border: 1px solid #000; font-weight: bold; text-align: center;">${c.code}</td>
        <td style="border: 1px solid #000; text-align: left;">${c.name}</td>
        <td style="border: 1px solid #000; text-align: right; font-weight: bold;">${c.tong_ton}</td>
        <td style="border: 1px solid #000; text-align: right; color: #dc2626; font-weight: bold;">${c.ton_qua_han}</td>
        <td style="border: 1px solid #000; text-align: right;">${c.ton_30_ngay || 0}</td>
        <td style="border: 1px solid #000; text-align: right; font-weight: bold; color: ${c.thuc_hien_ngay > 0 ? "#16a34a" : "#dc2626"};">${c.thuc_hien_ngay}</td>
        <td style="border: 1px solid #000; text-align: right;">${Math.round(c.ty_le_ht_ngay * 100)}%</td>
        <td style="border: 1px solid #000; text-align: center;">${c.danh_gia || "Đạt"}</td>
      </tr>
    `).join("");

    const ps = dataset.province_summary;
    const subtotalRow = `
      <tr style="background-color: #FEF3C7; font-weight: bold;">
        <td colspan="3" style="border: 1px solid #000; text-align: center;">TỔNG CỘNG TOÀN TỈNH</td>
        <td style="border: 1px solid #000; text-align: right;">${ps.tong_ton}</td>
        <td style="border: 1px solid #000; text-align: right; color: #dc2626;">${ps.ton_qua_han}</td>
        <td style="border: 1px solid #000; text-align: right;">${ps.ton_tren_30_ngay}</td>
        <td style="border: 1px solid #000; text-align: right; color: #16a34a;">${ps.thuc_hien_ngay}</td>
        <td style="border: 1px solid #000; text-align: right;">-</td>
        <td style="border: 1px solid #000; text-align: center;">-</td>
      </tr>
    `;

    return `
      <div style="font-family: Arial, sans-serif; font-size: 11px;">
        <h4 style="margin-bottom: 8px; color: #1E3A8A;">BẢNG TỔNG HỢP ĐIỀU HÀNH WO TOÀN TỈNH — NGÀY ${dataset.report_date_str}</h4>
        <table border="1" cellspacing="0" cellpadding="4" style="border-collapse: collapse; border: 1px solid #000; width: 100%; text-align: center;">
          <tr style="background-color: #1E3A8A; color: #ffffff; font-weight: bold;">
            <th style="border: 1px solid #000;">STT</th>
            <th style="border: 1px solid #000;">Mã TT</th>
            <th style="border: 1px solid #000;">Trung tâm huyện</th>
            <th style="border: 1px solid #000;">Tổng tồn</th>
            <th style="border: 1px solid #000;">Quá hạn</th>
            <th style="border: 1px solid #000;">> 30N</th>
            <th style="border: 1px solid #000;">TH Ngày</th>
            <th style="border: 1px solid #000;">Tỷ lệ HT</th>
            <th style="border: 1px solid #000;">Đánh giá</th>
          </tr>
          ${rows}
          ${subtotalRow}
        </table>
      </div>
    `;
  };

  const buildProvinceTableTsv = () => {
    if (!dataset) return "";
    const headers = ["STT", "Mã TT", "Trung tâm", "Tổng tồn", "Quá hạn", "Tồn > 30N", "TH Ngày", "Tỷ lệ HT", "Đánh giá"];
    const lines = [
      `BẢNG TỔNG HỢP ĐIỀU HÀNH WO TOÀN TỈNH — NGÀY ${dataset.report_date_str}`,
      headers.join("\t")
    ];

    dataset.centers.forEach((c, idx) => {
      lines.push([
        idx + 1,
        c.code,
        c.name,
        c.tong_ton,
        c.ton_qua_han,
        c.ton_30_ngay || 0,
        c.thuc_hien_ngay,
        `${Math.round(c.ty_le_ht_ngay * 100)}%`,
        c.danh_gia || "Đạt"
      ].join("\t"));
    });

    const ps = dataset.province_summary;
    lines.push(["Tổng cộng", "NAN", "Toàn tỉnh", ps.tong_ton, ps.ton_qua_han, ps.ton_tren_30_ngay, ps.thuc_hien_ngay, "", ""].join("\t"));

    return lines.join("\n");
  };

  const handleCopyTableConfirm = async (mode: ClipboardCopyMode) => {
    const html = buildProvinceTableHtml();
    const tsv = buildProvinceTableTsv();
    return await copyFormattedTable({
      element: tableRef.current,
      htmlContent: html,
      textContent: tsv,
      tsvContent: tsv,
      mode
    });
  };

  if (!dataset) {
    return (
      <div className="py-16 text-center max-w-md mx-auto">
        <FileText className="w-12 h-12 text-muted mx-auto mb-3" />
        <h3 className="text-base font-semibold text-foreground">Chưa có dữ liệu báo cáo</h3>
        <p className="text-xs text-muted mt-1">Vui lòng nạp tệp Excel điều hành trước khi tạo báo cáo toàn tỉnh.</p>
        <div className="mt-4">
          <Button onClick={() => setCurrentRoute("import")}>Đến trang Nhập dữ liệu</Button>
        </div>
      </div>
    );
  }

  const ps = dataset.province_summary;

  return (
    <div className="space-y-6">
      {/* ========================================================
          PHẦN TOP: Thông tin nguồn, Trạng thái & Action Bar
          ======================================================== */}
      <div className="bg-surface border border-border rounded-2xl p-5 shadow-xs space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-primary animate-pulse" />
              <span className="text-[11px] font-bold text-primary uppercase tracking-wider">
                Viettel Operations — NAN_DHKT
              </span>
            </div>
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-foreground">
              Báo cáo Điều hành WO Toàn tỉnh (Module A)
            </h1>
            <div className="flex items-center flex-wrap gap-2 text-xs text-muted mt-1.5">
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-primary" />
                Ngày báo cáo: <strong className="text-foreground">{dataset.report_date_str}</strong>
              </span>
              <span>•</span>
              <span className="truncate max-w-md">
                Tệp nguồn: <span className="font-mono text-foreground text-[11px]">{dataset.file_path}</span>
              </span>
            </div>
          </div>

          {/* Action Toolbar */}
          <div className="flex items-center flex-wrap gap-2.5">
            <Button
              variant="outline"
              size="sm"
              onClick={handlePickOtherFile}
              icon={<FolderOpen className="w-4 h-4 text-primary" />}
            >
              Chọn file khác
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsCopyTableModalOpen(true)}
              icon={<TableIcon className="w-4 h-4 text-primary" />}
            >
              Copy bảng tổng hợp
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsExportModalOpen(true)}
              icon={<Download className="w-4 h-4 text-primary" />}
            >
              Xuất Excel
            </Button>

            <Button
              size="sm"
              onClick={handleCopyReportText}
              icon={copiedText ? <Check className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
            >
              {copiedText ? "Đã copy nội dung" : "Copy nội dung toàn tỉnh"}
            </Button>
          </div>
        </div>

        {/* Validation Status Indicator */}
        <div className="flex items-center justify-between flex-wrap gap-2 pt-3 border-t border-border text-xs">
          <div className="flex items-center gap-2">
            <span className="text-muted">Trạng thái xác thực:</span>
            {ps.has_discrepancy ? (
              <Badge variant="warning" size="sm">
                Cảnh báo sai lệch dòng tổng cộng
              </Badge>
            ) : (
              <Badge variant="success" size="sm">
                Toàn vẹn (Khớp 14 trung tâm huyện)
              </Badge>
            )}
          </div>
          <div className="text-muted text-[11px]">
            Phát hiện các sheet: <span className="font-mono text-foreground">{dataset.detected_sheets.join(", ")}</span>
          </div>
        </div>

        {ps.has_discrepancy && (
          <div className="p-3.5 rounded-xl bg-warning-bg border border-warning/30 flex items-start gap-2.5 text-xs text-foreground">
            <AlertTriangle className="w-4 h-4 text-warning shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold text-warning mb-0.5">Chi tiết sai lệch dòng tổng cộng (Dòng 3):</div>
              <div>{ps.discrepancy_details}</div>
            </div>
          </div>
        )}
      </div>

      {/* ========================================================
          PHẦN SUMMARY: 4 KPI Cards Nổi bật
          ======================================================== */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard
          title="Tổng WO tồn"
          value={`${ps.tong_ton} WO`}
          subtitle="Toàn tỉnh đang tồn đọng"
          variant="default"
          icon={<FileText className="w-4 h-4" />}
        />
        <KpiCard
          title="WO quá hạn"
          value={`${ps.ton_qua_han} WO`}
          subtitle={`${Math.round((ps.ton_qua_han / (ps.tong_ton || 1)) * 100)}% trên tổng tồn`}
          variant="danger"
          icon={<AlertTriangle className="w-4 h-4" />}
        />
        <KpiCard
          title="WO quá hạn > 30 ngày"
          value={`${ps.ton_tren_30_ngay} WO`}
          subtitle={ps.overdue_30_centers.map(([c, n]) => `${c}:${n}`).join(", ") || "Không có huyện tồn >30N"}
          variant="warning"
          icon={<Clock className="w-4 h-4" />}
        />
        <KpiCard
          title="Thực hiện trong ngày"
          value={`${ps.thuc_hien_ngay} WO`}
          subtitle="Tiến độ hoàn thành ngày"
          variant="success"
          icon={<CheckCircle2 className="w-4 h-4" />}
        />
      </div>

      {/* ========================================================
          PHẦN CENTER RANKING: Bảng 14 Trung tâm huyện & Ranking
          ======================================================== */}
      <Card
        header={
          <div className="flex items-center justify-between w-full flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <Building className="w-4 h-4 text-primary" />
              <h3 className="text-sm font-bold text-foreground">
                Bảng Thống kê & Xếp hạng 14 Trung tâm Huyện
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsCopyTableModalOpen(true)}
                icon={<Copy className="w-3.5 h-3.5" />}
              >
                Copy bảng xếp hạng
              </Button>
            </div>
          </div>
        }
        noPadding
      >
        {/* Top 5 Banner */}
        <div className="p-3 bg-background border-b border-border flex items-center justify-between flex-wrap gap-2 text-xs">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-danger" />
            <span className="text-muted">Top 5 Trung tâm tồn cao nhất:</span>
            <span className="font-bold text-foreground tracking-wider bg-surface px-2 py-0.5 rounded border border-border">
              {ps.top_centers.join(", ")}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-muted">Cảnh báo tồn &gt; 30 ngày:</span>
            <span className="font-bold text-danger">
              {ps.overdue_30_centers.map(([c, n]) => `(${c}:${n})`).join(" ") || "0 huyện"}
            </span>
          </div>
        </div>

        {/* 14 Centers Table with Horizontal Scroll */}
        <div ref={tableRef} className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-surface border-b border-border text-muted font-semibold text-[11px] uppercase tracking-wider">
                <th className="py-2.5 px-3 text-center w-12">STT</th>
                <th className="py-2.5 px-3 text-center">Mã TT</th>
                <th className="py-2.5 px-3">Tên Trung tâm</th>
                <th className="py-2.5 px-3 text-right">Tổng tồn</th>
                <th className="py-2.5 px-3 text-right text-danger">Quá hạn</th>
                <th className="py-2.5 px-3 text-right text-warning">Tồn &gt;30N</th>
                <th className="py-2.5 px-3 text-right text-success font-bold">TH Ngày</th>
                <th className="py-2.5 px-3 text-right">Tỷ lệ HT</th>
                <th className="py-2.5 px-3 text-center">Đánh giá</th>
                <th className="py-2.5 px-3 text-center w-28">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {dataset.centers.map((c, idx) => {
                const isTop5 = ps.top_centers.includes(c.code);
                const has30Overdue = (c.ton_30_ngay || 0) > 0;
                return (
                  <tr
                    key={c.code}
                    className="hover:bg-item-hover transition-colors group text-foreground"
                  >
                    <td className="py-2 px-3 text-center text-muted font-mono">{idx + 1}</td>
                    <td className="py-2 px-3 text-center font-bold">
                      <span className={`px-1.5 py-0.5 rounded text-[11px] ${
                        isTop5 ? "bg-danger-bg text-danger font-bold" : "bg-secondary text-muted"
                      }`}>
                        {c.code}
                      </span>
                    </td>
                    <td className="py-2 px-3 font-medium">
                      <div className="flex items-center gap-1.5">
                        <span>{c.name}</span>
                        {has30Overdue && (
                          <span className="w-2 h-2 rounded-full bg-warning" title="Có WO > 30 ngày" />
                        )}
                      </div>
                    </td>
                    <td className="py-2 px-3 text-right font-bold">{c.tong_ton}</td>
                    <td className="py-2 px-3 text-right font-bold text-danger">{c.ton_qua_han}</td>
                    <td className="py-2 px-3 text-right text-warning font-semibold">
                      {c.ton_30_ngay > 0 ? c.ton_30_ngay : "-"}
                    </td>
                    <td className="py-2 px-3 text-right font-bold text-success">{c.thuc_hien_ngay}</td>
                    <td className="py-2 px-3 text-right font-mono text-[11px]">
                      {Math.round(c.ty_le_ht_ngay * 100)}%
                    </td>
                    <td className="py-2 px-3 text-center">
                      <Badge variant={c.danh_gia === "Chưa đạt" ? "danger" : "success"} size="sm">
                        {c.danh_gia || "Đạt"}
                      </Badge>
                    </td>
                    <td className="py-2 px-3 text-center">
                      <button
                        onClick={() => setCurrentRoute("centers", c.code)}
                        className="text-primary hover:text-primary-hover font-semibold text-[11px] inline-flex items-center gap-1 cursor-pointer"
                      >
                        Báo cáo TT <ArrowRight className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
            {/* Subtotal Row */}
            <tfoot>
              <tr className="bg-primary-subtle/40 border-t-2 border-border font-bold text-foreground">
                <td colSpan={3} className="py-2.5 px-3 text-center text-primary uppercase tracking-wider text-[11px]">
                  Tổng cộng toàn tỉnh (14 TT)
                </td>
                <td className="py-2.5 px-3 text-right">{ps.tong_ton}</td>
                <td className="py-2.5 px-3 text-right text-danger">{ps.ton_qua_han}</td>
                <td className="py-2.5 px-3 text-right text-warning">{ps.ton_tren_30_ngay}</td>
                <td className="py-2.5 px-3 text-right text-success">{ps.thuc_hien_ngay}</td>
                <td className="py-2.5 px-3 text-right">-</td>
                <td className="py-2.5 px-3 text-center">-</td>
                <td className="py-2.5 px-3 text-center">-</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </Card>

      {/* ========================================================
          PHẦN REPORT PREVIEW: Thiết lập & Soạn thông báo điều hành
          ======================================================== */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Inputs (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <Card
            header={
              <div className="flex items-center justify-between w-full">
                <h3 className="text-sm font-semibold text-foreground">Cấu hình Nội dung Điều hành</h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => generateReport(recipient, notification, deadlineQh, deadlineMonth)}
                  icon={<RotateCcw className="w-3.5 h-3.5" />}
                  title="Sinh lại nội dung từ dữ liệu chuẩn"
                >
                  Tạo lại
                </Button>
              </div>
            }
          >
            <div className="space-y-4 text-xs">
              <div>
                <label className="font-medium text-foreground block mb-1">Người nhận thông báo:</label>
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
                  <label className="font-medium text-foreground block mb-1">Hạn chót WO quá hạn:</label>
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
                  <label className="font-medium text-foreground block mb-1">Hạn chót WO tháng:</label>
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
                <label className="font-medium text-foreground block mb-1">Đoạn văn điều hành chỉ đạo:</label>
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

              <div className="pt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSaveTemplate}
                  icon={<BookmarkPlus className="w-3.5 h-3.5 text-primary" />}
                >
                  Lưu làm mẫu thông báo
                </Button>
              </div>
            </div>
          </Card>
        </div>

        {/* Right Live Preview (7 cols) */}
        <div className="lg:col-span-7">
          <Card
            header={
              <div className="flex items-center justify-between w-full">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-foreground">Xem trước Tin nhắn Điều hành TAMMI</h3>
                  {isManuallyEdited && (
                    <Badge variant="warning" size="sm">
                      Đã sửa thủ công
                    </Badge>
                  )}
                </div>
                <Button
                  size="sm"
                  onClick={handleCopyReportText}
                  icon={copiedText ? <Check className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
                >
                  {copiedText ? "Đã copy" : "Copy nội dung"}
                </Button>
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
                className="w-full bg-background border border-border rounded-xl p-4 font-mono text-xs text-foreground leading-relaxed focus:outline-none focus:ring-2 focus:ring-primary/20 resize-none select-text"
              />
            </div>
            <div className="px-5 py-3 border-t border-border bg-background/50 flex items-center justify-between text-xs text-muted">
              <span>Nội dung đã sửa thủ công sẽ được bảo toàn tuyệt đối, không bị tự động ghi đè.</span>
              <button
                onClick={() => generateReport(recipient, notification, deadlineQh, deadlineMonth)}
                className="text-primary hover:underline font-semibold cursor-pointer"
              >
                Khôi phục bản gốc
              </button>
            </div>
          </Card>
        </div>
      </div>

      {/* Export Modal Dialog */}
      <ExportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        reportType="executive_excel"
        previewText={reportText}
      />

      {/* Copy Mode Modal Dialog */}
      <CopyModeModal
        isOpen={isCopyTableModalOpen}
        onClose={() => setIsCopyTableModalOpen(false)}
        title="Sao chép Bảng Điều hành Toàn tỉnh cho TAMMI"
        onConfirmCopy={handleCopyTableConfirm}
      />
    </div>
  );
};
