import React, { useState, useEffect } from "react";
import { bridge } from "../../services/bridge";
import { useAppStore } from "../../stores/appStore";
import { Modal } from "../ui/Modal";
import { Button } from "../ui/Button";
import {
  Download,
  FolderOpen,
  FileSpreadsheet,
  Check,
  Copy,
  ExternalLink,
  AlertCircle,
  FileText
} from "lucide-react";

export interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  reportType: "executive_excel" | "thft_excel" | "center_docx";
  centerCode?: string;
  positionFilter?: string;
  previewText?: string;
}

export const ExportModal: React.FC<ExportModalProps> = ({
  isOpen,
  onClose,
  reportType,
  centerCode,
  positionFilter = "Tất cả",
  previewText = ""
}) => {
  const { dataset, addToast } = useAppStore();

  const computeDefaultFilename = () => {
    const dateStr = dataset?.report_date_str?.replace(/\//g, "") || new Date().toISOString().slice(0, 10).replace(/-/g, "");

    let posSuffix = "";
    const pUpper = (positionFilter || "").toUpperCase();
    if (pUpper.includes("DM")) {
      posSuffix = "_NVDM";
    } else if (pUpper.includes("TRẠM") || pUpper.includes("TRAM")) {
      posSuffix = "_NVNhaTram";
    }

    if (reportType === "executive_excel") {
      return `BaoCao_WO_${dateStr}.xlsx`;
    } else if (reportType === "center_docx" && centerCode) {
      return `BaoCao_FT_${centerCode}_${dateStr}.docx`;
    } else {
      if (centerCode && centerCode !== "ALL") {
        return `BaoCao_THFT_${centerCode}_${dateStr}${posSuffix}.xlsx`;
      } else {
        return `BaoCao_THFT_${dateStr}${posSuffix}.xlsx`;
      }
    }
  };

  const [outputDir, setOutputDir] = useState("C:\\Reports");
  const [filename, setFilename] = useState(computeDefaultFilename);
  const [rememberDir, setRememberDir] = useState(true);
  const [autoOpenFile, setAutoOpenFile] = useState(true);
  const [autoOpenFolder, setAutoOpenFolder] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [exportResult, setExportResult] = useState<{
    success: boolean;
    outputPath?: string;
    outputPaths?: string[];
    error?: string;
  } | null>(null);

  // Synchronize on modal open without flickering
  useEffect(() => {
    if (!isOpen) {
      setExportResult(null);
      return;
    }

    // Set suggested filename immediately
    setFilename(computeDefaultFilename());

    // Load saved default directory from config silently
    bridge.getAppConfig().then((cfg) => {
      if (cfg && cfg.default_output_dir) {
        setOutputDir(cfg.default_output_dir);
      }
    }).catch(() => {});
  }, [isOpen]);

  const handlePickDirectory = async () => {
    try {
      const selected = await bridge.pickDirectory();
      if (selected && selected.trim()) {
        setOutputDir(selected);
      }
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi chọn thư mục", message: err.message });
    }
  };

  const handleExport = async () => {
    if (!outputDir || !outputDir.trim()) {
      addToast({ type: "warning", title: "Chưa chọn thư mục", message: "Vui lòng chỉ định thư mục lưu báo cáo." });
      return;
    }
    if (!filename || !filename.trim()) {
      addToast({ type: "warning", title: "Chưa đặt tên file", message: "Vui lòng nhập tên file xuất hợp lệ." });
      return;
    }

    setIsExporting(true);
    setExportResult(null);

    try {
      const params: any = {
        output_dir: outputDir,
        custom_filename: filename,
        preview_text: previewText,
        remember_dir: rememberDir,
        auto_open_file: autoOpenFile,
        auto_open_folder: autoOpenFolder
      };

      if (reportType === "thft_excel") {
        params.position_filter = positionFilter;
        if (centerCode && centerCode !== "ALL") {
          params.selected_centers = [centerCode];
          params.separate_files = false;
        }
      } else if (reportType === "center_docx") {
        params.center_code = centerCode;
        params.notification = previewText;
      }

      const res = await bridge.exportReport(reportType, params);
      setExportResult(res);

      if (res.success) {
        addToast({
          type: "success",
          title: "Xuất file thành công",
          message: `Tệp đã được lưu vào: ${res.output_path || res.output_paths?.[0] || outputDir}`
        });
      } else {
        addToast({
          type: "error",
          title: "Xuất file thất bại",
          message: res.error || "Không thể xuất file. Vui lòng kiểm tra quyền ghi hoặc đóng file nếu đang mở."
        });
      }
    } catch (err: any) {
      setExportResult({ success: false, error: err.message });
      addToast({ type: "error", title: "Lỗi xuất file", message: err.message });
    } finally {
      setIsExporting(false);
    }
  };

  const primaryPath = exportResult?.outputPath || exportResult?.outputPaths?.[0] || "";

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Xuất Báo Cáo Excel / Word"
      size="md"
    >
      <div className="space-y-4 text-xs">
        {/* Info Badges */}
        <div className="bg-background rounded-xl p-3 border border-border flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <span className="text-muted">Loại:</span>
            <span className="font-semibold text-foreground">
              {reportType === "executive_excel"
                ? "Điều hành WO Toàn tỉnh (Module A)"
                : reportType === "thft_excel"
                ? "Báo cáo Nhân viên FT (Module B)"
                : "Tài liệu Word Trung tâm"}
            </span>
          </div>
          {centerCode && (
            <div className="flex items-center gap-1.5">
              <span className="text-muted">Đơn vị:</span>
              <span className="bg-primary/10 text-primary font-bold px-2 py-0.5 rounded">
                {centerCode === "ALL" ? "Toàn tỉnh (14 TT)" : centerCode}
              </span>
            </div>
          )}
          {reportType === "thft_excel" && (
            <div className="flex items-center gap-1.5">
              <span className="text-muted">Bộ lọc:</span>
              <span className="bg-secondary text-foreground font-medium px-2 py-0.5 rounded">
                {positionFilter}
              </span>
            </div>
          )}
        </div>

        {/* Filename Field */}
        <div>
          <label className="font-medium text-foreground block mb-1">Tên file đầu ra:</label>
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={filename}
              onChange={(e) => setFilename(e.target.value)}
              className="flex-1 bg-surface border border-border-strong rounded-lg px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 font-mono text-xs"
            />
          </div>
        </div>

        {/* Directory Picker */}
        <div>
          <label className="font-medium text-foreground block mb-1">Thư mục lưu tệp:</label>
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={outputDir}
              onChange={(e) => setOutputDir(e.target.value)}
              placeholder="Chọn đường dẫn..."
              className="flex-1 bg-surface border border-border-strong rounded-lg px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 text-xs"
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handlePickDirectory}
              icon={<FolderOpen className="w-4 h-4 text-primary" />}
            >
              Chọn thư mục...
            </Button>
          </div>
        </div>

        {/* Export Options */}
        <div className="space-y-2 pt-1 border-t border-border">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={rememberDir}
              onChange={(e) => setRememberDir(e.target.checked)}
              className="rounded text-primary focus:ring-primary/30 w-3.5 h-3.5 accent-primary"
            />
            <span className="text-muted text-[11px]">Ghi nhớ thư mục này làm mặc định trong cài đặt</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={autoOpenFile}
              onChange={(e) => setAutoOpenFile(e.target.checked)}
              className="rounded text-primary focus:ring-primary/30 w-3.5 h-3.5 accent-primary"
            />
            <span className="text-muted text-[11px]">Tự động mở file Excel/Word sau khi xuất xong</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={autoOpenFolder}
              onChange={(e) => setAutoOpenFolder(e.target.checked)}
              className="rounded text-primary focus:ring-primary/30 w-3.5 h-3.5 accent-primary"
            />
            <span className="text-muted text-[11px]">Mở thư mục chứa file sau khi xuất</span>
          </label>
        </div>

        {/* Result & Actions Area */}
        {exportResult && (
          <div
            className={`p-3.5 rounded-xl border ${
              exportResult.success
                ? "bg-success-bg border-success/30 text-success"
                : "bg-danger-bg border-danger/30 text-danger"
            }`}
          >
            {exportResult.success ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2 font-bold text-xs text-foreground">
                  <Check className="w-4 h-4 text-success" />
                  <span>Đã xuất thành công:</span>
                </div>
                <div className="font-mono text-[11px] text-muted break-all bg-surface/70 p-2 rounded border border-border">
                  {primaryPath}
                </div>
                <div className="flex items-center gap-2 pt-1">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => bridge.openFile(primaryPath)}
                    icon={<ExternalLink className="w-3.5 h-3.5" />}
                  >
                    Mở tệp
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => bridge.openFolder(primaryPath)}
                    icon={<FolderOpen className="w-3.5 h-3.5" />}
                  >
                    Mở thư mục
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      navigator.clipboard.writeText(primaryPath);
                      addToast({ type: "info", message: "Đã chép đường dẫn tệp vào clipboard." });
                    }}
                    icon={<Copy className="w-3.5 h-3.5" />}
                  >
                    Chép đường dẫn
                  </Button>
                </div>
              </div>
            ) : (
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <div className="text-xs">
                  <div className="font-bold">Lỗi xuất tệp:</div>
                  <div className="text-[11px] mt-0.5 leading-relaxed">{exportResult.error}</div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Modal Buttons */}
        <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-border">
          <Button variant="outline" size="sm" onClick={onClose} disabled={isExporting}>
            {exportResult?.success ? "Đóng" : "Hủy"}
          </Button>

          <Button
            size="sm"
            onClick={handleExport}
            isLoading={isExporting}
            icon={<Download className="w-4 h-4" />}
          >
            {isExporting ? "Đang xuất..." : "Bắt đầu xuất"}
          </Button>
        </div>
      </div>
    </Modal>
  );
};
