import React, { useState, useEffect } from "react";
import { useAppStore } from "../stores/appStore";
import { bridge } from "../services/bridge";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import {
  Send,
  Copy,
  Download,
  Save,
  RotateCcw,
  AlertCircle,
  Check,
  FileText,
  Sliders,
  Layers
} from "lucide-react";

export const ReportBuilderPage: React.FC = () => {
  const { dataset, addToast, setCurrentRoute } = useAppStore();

  const [reportType, setReportType] = useState<string>("province");
  const [selectedCenter, setSelectedCenter] = useState<string>("");
  const [positionFilter, setPositionFilter] = useState<string>("Tất cả");
  const [recipient, setRecipient] = useState<string>("Kính gửi PGĐ @NAN PGĐ A THẮNG , TP @A Sơnpb1 TPKT NAN , TTH!");
  const [deadline, setDeadline] = useState<string>("05/10");
  const [meetingTime, setMeetingTime] = useState<string>("06:30");
  const [templateContent, setTemplateContent] = useState<string>("");
  const [renderedOutput, setRenderedOutput] = useState<string>("");
  const [unknownPlaceholders, setUnknownPlaceholders] = useState<string[]>([]);
  const [copied, setCopied] = useState<boolean>(false);

  const KNOWN_PLACEHOLDERS = [
    "{NGAY_BAO_CAO}",
    "{THANG}",
    "{NAM}",
    "{TONG_TON}",
    "{TON_QUA_HAN}",
    "{TON_TREN_30_NGAY}",
    "{CHI_TIET_TREN_30_NGAY}",
    "{TOP_5_TRUNG_TAM}",
    "{THUC_HIEN_NGAY}",
    "{TEN_HUYEN}",
    "{MA_HUYEN}",
    "{DANH_SACH_TAG}",
    "{HAN_HOAN_THANH}",
    "{GIO_HOP}",
    "{NGUOI_NHAN}",
    "{NOI_DUNG_THONG_BAO}"
  ];

  useEffect(() => {
    if (dataset && dataset.centers.length > 0 && !selectedCenter) {
      setSelectedCenter(dataset.centers[0].code);
    }
  }, [dataset]);

  useEffect(() => {
    // Set default template according to report type
    if (reportType === "province") {
      setTemplateContent(
        "{NGUOI_NHAN}\n\n" +
        "PVHKT kính gửi tiến độ cắt tồn wo tháng {THANG}\n" +
        "theo PGNV của Đ/c PGĐCN đến ngày {NGAY_BAO_CAO}\n\n" +
        "+Thực hiện ngày: {THUC_HIEN_NGAY} WO\n\n" +
        "- Tổng tồn: {TONG_TON} Wo, trong đó:\n" +
        "{TON_QUA_HAN} Wo tồn quá hạn,\n" +
        "{TON_TREN_30_NGAY} Wo tồn >30 ngày{CHI_TIET_TREN_30_NGAY}\n\n" +
        "- Tồn cao tại TT: {TOP_5_TRUNG_TAM}\n\n" +
        "Kính đề nghị TTH tồn wo:\n\n" +
        "Đóng Wo quá hạn trước 30/9. Đóng hết wo tháng {THANG} xong trước {HAN_HOAN_THANH}.\n\n" +
        "@mọi người"
      );
    } else if (reportType === "center_ft") {
      setTemplateContent(
        "FT tồn quá hạn wo đến ngày hôm nay {NGAY_BAO_CAO}, " +
        "khẩn trương hoàn thành trước {HAN_HOAN_THANH}. " +
        "FT không có tiến độ ngày sẽ triệu tập họp vào {GIO_HOP} ngày mai {DANH_SACH_TAG}"
      );
    } else if (reportType === "overdue_list") {
      setTemplateContent(
        "THÔNG BÁO WO QUÁ HẠN TẠI {TEN_HUYEN} ({MA_HUYEN})\n" +
        "Đến ngày {NGAY_BAO_CAO}, đơn vị có {TON_QUA_HAN} WO quá hạn.\n" +
        "Đề nghị các đồng chí xử lý dứt điểm trước {HAN_HOAN_THANH}."
      );
    }
  }, [reportType]);

  useEffect(() => {
    renderTemplate();
  }, [templateContent, reportType, selectedCenter, positionFilter, recipient, deadline, meetingTime, dataset]);

  const renderTemplate = () => {
    if (!dataset) return;
    const ps = dataset.province_summary;
    const center = dataset.centers.find((c) => c.code === selectedCenter) || dataset.centers[0];

    // Detect unknown placeholders: find all {...} in template
    const matches = templateContent.match(/\{[A-Z0-9_]+\}/g) || [];
    const unknowns: string[] = [];
    matches.forEach((m) => {
      if (!KNOWN_PLACEHOLDERS.includes(m) && !unknowns.includes(m)) {
        unknowns.push(m);
      }
    });
    setUnknownPlaceholders(unknowns);

    let output = templateContent;
    const tagString = center ? center.code : ""; // will be populated
    const detail30 = ps.overdue_30_centers.map(([c, n]) => `${c}:${n}`).join(", ");

    output = output.replace(/{NGUOI_NHAN}/g, recipient);
    output = output.replace(/{NGAY_BAO_CAO}/g, dataset.report_date_str);
    output = output.replace(/{THANG}/g, String(ps.month));
    output = output.replace(/{NAM}/g, String(ps.year));
    output = output.replace(/{TONG_TON}/g, String(center ? center.tong_ton : ps.tong_ton));
    output = output.replace(/{TON_QUA_HAN}/g, String(center ? center.ton_qua_han : ps.ton_qua_han));
    output = output.replace(/{TON_TREN_30_NGAY}/g, String(center ? center.ton_30_ngay : ps.ton_tren_30_ngay));
    output = output.replace(/{CHI_TIET_TREN_30_NGAY}/g, detail30 ? ` (${detail30})` : "");
    output = output.replace(/{TOP_5_TRUNG_TAM}/g, ps.top_centers.join(", "));
    output = output.replace(/{THUC_HIEN_NGAY}/g, String(center ? center.thuc_hien_ngay : ps.thuc_hien_ngay));
    output = output.replace(/{TEN_HUYEN}/g, center ? center.name : "Toàn tỉnh");
    output = output.replace(/{MA_HUYEN}/g, center ? center.code : "NAN");
    output = output.replace(/{HAN_HOAN_THANH}/g, deadline);
    output = output.replace(/{GIO_HOP}/g, meetingTime);

    setRenderedOutput(output);
  };

  const handleCopy = async () => {
    try {
      await bridge.copyToClipboard("text", { text: renderedOutput });
      setCopied(true);
      addToast({ type: "success", message: "Đã sao chép nội dung vào Clipboard" });
      setTimeout(() => setCopied(false), 2500);
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi sao chép", message: err.message });
    }
  };

  const handleSaveTemplate = async () => {
    try {
      await bridge.saveTemplate(
        `Mẫu ${reportType} (${new Date().toLocaleDateString()})`,
        reportType,
        templateContent
      );
      addToast({ type: "success", message: "Đã lưu mẫu báo cáo vào SQLite thành công" });
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi lưu mẫu", message: err.message });
    }
  };

  if (!dataset) {
    return (
      <div className="py-16 text-center max-w-md mx-auto">
        <Send className="w-12 h-12 text-muted mx-auto mb-3" />
        <h3 className="text-base font-semibold text-foreground">Chưa có dữ liệu</h3>
        <p className="text-xs text-muted mt-1">Vui lòng nạp tệp Excel điều hành trước.</p>
        <div className="mt-4">
          <Button onClick={() => setCurrentRoute("import")}>Đến trang Nhập dữ liệu</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Soạn Thảo & Tùy Biến Báo Cáo (Module E)
          </h1>
          <p className="text-xs text-muted mt-1">
            Hỗ trợ các placeholder an toàn: &#123;NGAY_BAO_CAO&#125;, &#123;TONG_TON&#125;, &#123;DANH_SACH_TAG&#125;, &#123;HAN_HOAN_THANH&#125;...
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={handleSaveTemplate}
            icon={<Save className="w-4 h-4" />}
          >
            Lưu mẫu này
          </Button>
          <Button
            size="sm"
            onClick={handleCopy}
            icon={copied ? <Check className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
          >
            {copied ? "Đã copy" : "Copy nội dung"}
          </Button>
        </div>
      </div>

      {/* Placeholder warning if unknown */}
      {unknownPlaceholders.length > 0 && (
        <div className="p-3.5 rounded-xl bg-warning-bg border border-warning/30 flex items-start gap-3 text-xs">
          <AlertCircle className="w-4 h-4 text-warning shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-warning">Phát hiện placeholder không xác định: </span>
            <span className="font-mono text-foreground">{unknownPlaceholders.join(", ")}</span>
            <p className="text-muted mt-0.5">Các thẻ này sẽ không được thay thế tự động và giữ nguyên dạng chữ.</p>
          </div>
        </div>
      )}

      {/* Configuration Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Form: Parameters & Template Editor (6 cols) */}
        <div className="lg:col-span-6 space-y-4">
          <Card
            header={
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-primary" />
                <h3 className="text-sm font-semibold text-foreground">Tham số Báo cáo</h3>
              </div>
            }
          >
            <div className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-medium text-foreground block mb-1">Loại báo cáo:</label>
                  <select
                    value={reportType}
                    onChange={(e) => setReportType(e.target.value)}
                    className="w-full bg-background border border-border-strong rounded-lg px-2.5 py-2 text-foreground focus:outline-none"
                  >
                    <option value="province">Điều hành toàn tỉnh</option>
                    <option value="center_ft">Báo cáo FT theo huyện</option>
                    <option value="overdue_list">Danh sách WO quá hạn</option>
                  </select>
                </div>

                <div>
                  <label className="font-medium text-foreground block mb-1">Áp dụng cho:</label>
                  <select
                    value={selectedCenter}
                    onChange={(e) => setSelectedCenter(e.target.value)}
                    disabled={reportType === "province"}
                    className="w-full bg-background border border-border-strong rounded-lg px-2.5 py-2 text-foreground focus:outline-none disabled:opacity-50"
                  >
                    {dataset.centers.map((c) => (
                      <option key={c.code} value={c.code}>
                        {c.code} - {c.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-medium text-foreground block mb-1">Hạn hoàn thành:</label>
                  <input
                    type="text"
                    value={deadline}
                    onChange={(e) => setDeadline(e.target.value)}
                    className="w-full bg-background border border-border-strong rounded-lg px-2.5 py-2 text-foreground focus:outline-none"
                  />
                </div>

                <div>
                  <label className="font-medium text-foreground block mb-1">Giờ họp triệu tập:</label>
                  <input
                    type="text"
                    value={meetingTime}
                    onChange={(e) => setMeetingTime(e.target.value)}
                    className="w-full bg-background border border-border-strong rounded-lg px-2.5 py-2 text-foreground focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="font-medium text-foreground block mb-1">Người nhận:</label>
                <input
                  type="text"
                  value={recipient}
                  onChange={(e) => setRecipient(e.target.value)}
                  className="w-full bg-background border border-border-strong rounded-lg px-2.5 py-2 text-foreground focus:outline-none"
                />
              </div>

              {/* Template Textarea */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="font-medium text-foreground">Mẫu nội dung (Template):</label>
                  <span className="text-[11px] text-muted">Bấm placeholder bên dưới để chèn</span>
                </div>
                <textarea
                  rows={10}
                  value={templateContent}
                  onChange={(e) => setTemplateContent(e.target.value)}
                  className="w-full bg-background border border-border rounded-lg p-3 font-mono text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 resize-none leading-relaxed"
                />
              </div>

              {/* Placeholders quick pills */}
              <div className="flex flex-wrap gap-1.5 pt-1">
                {KNOWN_PLACEHOLDERS.map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setTemplateContent((prev) => prev + " " + p)}
                    className="text-[10px] font-mono bg-background border border-border px-1.5 py-0.5 rounded text-muted hover:text-foreground hover:border-foreground/30 transition-colors cursor-pointer"
                  >
                    + {p}
                  </button>
                ))}
              </div>
            </div>
          </Card>
        </div>

        {/* Right: Live Result Preview (6 cols) */}
        <div className="lg:col-span-6">
          <Card
            header={
              <div className="flex items-center justify-between w-full">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-primary" />
                  <h3 className="text-sm font-semibold text-foreground">Kết quả Sau khi Thế chỗ (Live Preview)</h3>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleCopy}
                  icon={copied ? <Check className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
                >
                  {copied ? "Đã copy" : "Copy"}
                </Button>
              </div>
            }
            noPadding
          >
            <div className="p-4">
              <textarea
                readOnly
                rows={18}
                value={renderedOutput}
                className="w-full bg-background border border-border rounded-lg p-4 font-mono text-xs text-foreground leading-relaxed focus:outline-none resize-none select-text"
              />
            </div>
            <div className="px-5 py-3 border-t border-border bg-background/50 text-[11px] text-muted">
              Số liệu tự động cập nhật theo thời gian thực từ dataset đang nạp.
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
