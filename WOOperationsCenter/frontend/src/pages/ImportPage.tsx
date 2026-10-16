import React, { useState, useEffect } from "react";
import { useAppStore } from "../stores/appStore";
import { bridge, DatasetSummary } from "../services/bridge";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import {
  UploadCloud,
  FileSpreadsheet,
  CheckCircle2,
  AlertCircle,
  FileCheck,
  Clock,
  ArrowRight,
  ShieldAlert,
  Layers,
  Sparkles
} from "lucide-react";

export const ImportPage: React.FC = () => {
  const { dataset, setDataset, setLoading, isLoading, addToast, setCurrentRoute } = useAppStore();
  const [recentFiles, setRecentFiles] = useState<string[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [progressMsg, setProgressMsg] = useState("");
  const [progressPct, setProgressPct] = useState(0);

  useEffect(() => {
    bridge.getAppConfig().then((cfg) => {
      if (cfg && cfg.recent_files) {
        setRecentFiles(cfg.recent_files);
      }
    });

    const unsubscribe = bridge.onProgress((pct, msg) => {
      setProgressPct(pct);
      setProgressMsg(msg);
    });
    return unsubscribe;
  }, []);

  const handleSelectFile = async () => {
    try {
      const selectedPath = await bridge.pickExcelFile();
      if (!selectedPath) return;
      await processFile(selectedPath);
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi nạp tệp", message: err.message });
    }
  };

  const processFile = async (filePath: string) => {
    setLoading(true);
    setProgressPct(10);
    setProgressMsg("Đang chuẩn bị nạp tệp...");
    try {
      const ds = await bridge.loadExcelDataset(filePath);
      setDataset(ds);
      addToast({
        type: "success",
        title: "Nạp tệp thành công",
        message: `Đã đọc thành công ${ds.total_employees} FT và ${ds.total_work_orders} WO quá hạn từ ${ds.centers.length} trung tâm huyện.`
      });
      // Refresh recent files
      const cfg = await bridge.getAppConfig();
      if (cfg && cfg.recent_files) setRecentFiles(cfg.recent_files);
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi phân tích Excel",
        message: err.message || "Tệp Excel không đúng cấu trúc"
      });
    } finally {
      setLoading(false);
      setProgressPct(0);
      setProgressMsg("");
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      // On desktop WebEngine, path property is available on file
      const path = (file as any).path || file.name;
      await processFile(path);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          Nhập & Xác thực Dữ liệu Excel
        </h1>
        <p className="text-xs text-muted mt-1">
          Hỗ trợ tệp ĐH WO UT1 nguồn chứa các sheet: TH TTH, THFT, WO. Chế độ chỉ đọc bảo vệ 100% dữ liệu gốc.
        </p>
      </div>

      {/* Drag & Drop Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleSelectFile}
        className={`border-2 border-dashed rounded-2xl p-10 text-center transition-all cursor-pointer select-none ${
          isDragging
            ? "border-primary bg-primary/5 scale-[1.01]"
            : "border-border hover:border-foreground/30 bg-surface"
        }`}
      >
        <div className="w-16 h-16 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mx-auto mb-4">
          <UploadCloud className="w-8 h-8" />
        </div>
        <h3 className="text-base font-semibold text-foreground">
          Kéo thả tệp Excel điều hành vào đây, hoặc nhấn để chọn
        </h3>
        <p className="text-xs text-muted mt-1.5 max-w-md mx-auto leading-relaxed">
          Định dạng hỗ trợ: <span className="font-semibold text-foreground">.xlsx, .xlsm</span>. Hệ thống tự động phát hiện các worksheet, bỏ qua bảng nhật ký dung lượng lớn (Logfile) để tối ưu bộ nhớ.
        </p>
        <div className="mt-5">
          <Button variant="primary" size="md" icon={<FileSpreadsheet className="w-4 h-4" />}>
            Chọn tệp từ máy tính
          </Button>
        </div>
      </div>

      {/* Progress Indicator */}
      {isLoading && (
        <Card>
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium text-foreground">{progressMsg || "Đang xử lý dữ liệu..."}</span>
              <span className="font-semibold text-primary">{progressPct}%</span>
            </div>
            <div className="w-full bg-secondary h-2 rounded-full overflow-hidden">
              <div
                className="bg-primary h-full transition-all duration-300"
                style={{ width: `${progressPct}%` }}
              />
            </div>
          </div>
        </Card>
      )}

      {/* Active Dataset Inspection */}
      {dataset && (
        <Card
          header={
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-2.5">
                <FileCheck className="w-5 h-5 text-success" />
                <h3 className="text-sm font-semibold text-foreground">Thông tin Tệp Dữ liệu Đang Hoạt Động</h3>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentRoute("dashboard")}
                icon={<ArrowRight className="w-4 h-4" />}
                iconPosition="right"
              >
                Vào Bảng Điều Hành
              </Button>
            </div>
          }
        >
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
            <div className="bg-background p-3 rounded-lg">
              <div className="text-muted mb-1">Đường dẫn tệp:</div>
              <div className="font-semibold text-foreground truncate" title={dataset.file_path}>
                {dataset.file_path}
              </div>
            </div>

            <div className="bg-background p-3 rounded-lg">
              <div className="text-muted mb-1">Thời điểm báo cáo:</div>
              <div className="font-semibold text-foreground">
                {dataset.report_date_str} ({dataset.day_month_str})
              </div>
            </div>

            <div className="bg-background p-3 rounded-lg">
              <div className="text-muted mb-1">Số trung tâm phát hiện:</div>
              <div className="font-semibold text-foreground">
                {dataset.centers.length} Trung tâm Huyện
              </div>
            </div>

            <div className="bg-background p-3 rounded-lg">
              <div className="text-muted mb-1">Mã vân tay (Fingerprint):</div>
              <div className="font-mono font-semibold text-muted text-[11px]">
                {dataset.file_fingerprint}
              </div>
            </div>
          </div>

          {/* Detected Sheets Badges */}
          <div className="mt-4 pt-4 border-t border-border flex items-center justify-between flex-wrap gap-2 text-xs">
            <div className="flex items-center gap-2 text-muted">
              <Layers className="w-4 h-4" />
              <span>Các sheet được kích hoạt:</span>
            </div>
            <div className="flex items-center gap-2">
              {dataset.detected_sheets.map((s) => (
                <Badge
                  key={s}
                  variant={s === "Logfile" ? "neutral" : "primary"}
                  size="sm"
                >
                  {s} {s === "Logfile" ? "(Đã tối ưu)" : ""}
                </Badge>
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* Recent Files List */}
      {recentFiles.length > 0 && (
        <Card
          header={
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-muted" />
              <h3 className="text-sm font-semibold text-foreground">Tệp đã mở gần đây</h3>
            </div>
          }
          noPadding
        >
          <div className="divide-y divide-border">
            {recentFiles.map((fPath, idx) => (
              <div
                key={idx}
                className="px-5 py-3 flex items-center justify-between gap-4 hover:bg-item-hover transition-colors text-xs"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <FileSpreadsheet className="w-4 h-4 text-muted shrink-0" />
                  <span className="font-medium text-foreground truncate" title={fPath}>
                    {fPath}
                  </span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => processFile(fPath)}
                  disabled={isLoading}
                >
                  Nạp lại
                </Button>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};
