import React, { useState, useEffect, useRef } from "react";
import { bridge } from "../services/bridge";
import { useAppStore } from "../stores/appStore";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { CopyModeModal } from "../components/modals/CopyModeModal";
import { copyFormattedTable, ClipboardCopyMode } from "../services/clipboardHelper";
import {
  FileSpreadsheet,
  FolderOpen,
  Copy,
  Table as TableIcon,
  Image as ImageIcon,
  Check,
  RefreshCw,
  Search,
  Layers,
  Info,
  Maximize2
} from "lucide-react";

export const ExcelCopierPage: React.FC = () => {
  const { dataset, addToast } = useAppStore();

  const [filePath, setFilePath] = useState<string>("");
  const [sheets, setSheets] = useState<string[]>([]);
  const [selectedSheet, setSelectedSheet] = useState<string>("");
  const [rangeStr, setRangeStr] = useState<string>("A1:T30");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [previewData, setPreviewData] = useState<any>(null);
  const [copiedMode, setCopiedMode] = useState<string | null>(null);

  const previewTableRef = useRef<HTMLDivElement>(null);

  // Initialize with current dataset file path or default sample
  useEffect(() => {
    if (dataset?.file_path) {
      setFilePath(dataset.file_path);
      loadSheetList(dataset.file_path);
    } else {
      bridge.getAppConfig().then((cfg) => {
        const recent = cfg?.recent_files?.[0] || "samples/BaoCao_THFT_20261015_NVDM.xlsx";
        setFilePath(recent);
        loadSheetList(recent);
      });
    }
  }, [dataset]);

  const loadSheetList = async (targetPath: string) => {
    if (!targetPath) return;
    setIsLoading(true);
    try {
      const res = await bridge.getExcelSheetNames(targetPath);
      if (res.success && res.sheets.length > 0) {
        setSheets(res.sheets);
        const initialSheet = res.sheets[0];
        setSelectedSheet(initialSheet);
        loadRangeData(targetPath, initialSheet, rangeStr);
      } else {
        setSheets([]);
        setPreviewData(null);
      }
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi đọc danh sách sheet", message: err.message });
    } finally {
      setIsLoading(false);
    }
  };

  const loadRangeData = async (fPath: string, sName: string, rStr: string) => {
    if (!fPath || !sName) return;
    setIsLoading(true);
    try {
      const res = await bridge.parseExcelRange(fPath, sName, rStr);
      if (res.success && res.data) {
        setPreviewData(res.data);
      } else {
        throw new Error(res.error || "Không thể phân tích dữ liệu vùng ô");
      }
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi tải vùng ô Excel", message: err.message });
    } finally {
      setIsLoading(false);
    }
  };

  const handlePickFile = async () => {
    try {
      const selected = await bridge.pickExcelFile();
      if (selected && selected.trim()) {
        setFilePath(selected);
        loadSheetList(selected);
      }
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi chọn file", message: err.message });
    }
  };

  const handleSheetChange = (sheet: string) => {
    setSelectedSheet(sheet);
    loadRangeData(filePath, sheet, rangeStr);
  };

  const handleRangeSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    loadRangeData(filePath, selectedSheet, rangeStr);
  };

  const handleCopyMode = async (mode: ClipboardCopyMode) => {
    if (!filePath || !selectedSheet || !previewData) {
      addToast({ type: "warning", message: "Chưa có dữ liệu để sao chép." });
      return;
    }

    try {
      const ok = await copyFormattedTable({
        element: previewTableRef.current,
        htmlContent: previewData.html_table,
        textContent: previewData.plain_text,
        tsvContent: previewData.tsv_text,
        mode
      });

      if (ok) {
        setCopiedMode(mode);
        addToast({
          type: "success",
          title: "Đã sao chép vào Clipboard",
          message: `Đã nạp vùng [${previewData.range_str}] sheet [${selectedSheet}] ở định dạng: ${
            mode === "html"
              ? "Bảng có định dạng (HTML)"
              : mode === "image"
              ? "Ảnh PNG"
              : mode === "tsv"
              ? "Dữ liệu Excel (TSV)"
              : "Văn bản"
          }. Bạn có thể mở TAMMI và nhấn Ctrl+V.`
        });
        setTimeout(() => setCopiedMode(null), 2500);
      } else {
        throw new Error("Không thể ghi vào hệ thống Clipboard.");
      }
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi sao chép", message: err.message });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Description */}
      <div className="bg-surface border border-border rounded-2xl p-5 shadow-xs space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[11px] font-bold text-primary uppercase tracking-wider">
                Excel-to-TAMMI Engine (Flow B)
              </span>
            </div>
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-foreground">
              Công cụ Trích xuất & Sao chép từ File Excel
            </h1>
            <p className="text-xs text-muted mt-1">
              Mở trực tiếp file báo cáo Excel đã xuất, chọn sheet huyện và vùng ô, xem trước và nhấn 1 nút để dán thẳng vào TAMMI.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <Button
              variant="outline"
              size="sm"
              onClick={handlePickFile}
              icon={<FolderOpen className="w-4 h-4 text-primary" />}
            >
              Chọn tệp Excel khác...
            </Button>
          </div>
        </div>

        {/* Current File Banner */}
        <div className="flex items-center gap-2 text-xs text-foreground bg-background p-2.5 rounded-xl border border-border">
          <FileSpreadsheet className="w-4 h-4 text-primary shrink-0" />
          <span className="text-muted shrink-0">Tệp đang chọn:</span>
          <span className="font-mono text-[11px] truncate">{filePath || "Chưa chọn tệp"}</span>
        </div>
      </div>

      {/* Control Panel: Sheets & Range */}
      <div className="bg-surface border border-border rounded-2xl p-5 shadow-xs space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          {/* Sheet Selector */}
          <div className="space-y-1.5 flex-1">
            <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-primary" />
              Chọn Worksheet ({sheets.length} sheets):
            </label>
            <div className="flex items-center flex-wrap gap-1.5 max-h-24 overflow-y-auto">
              {sheets.map((s) => (
                <button
                  key={s}
                  onClick={() => handleSheetChange(s)}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                    selectedSheet === s
                      ? "bg-primary text-primary-foreground shadow-xs"
                      : "bg-background border border-border hover:border-border-strong text-muted hover:text-foreground"
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Range Config Form */}
          <form onSubmit={handleRangeSubmit} className="flex items-end gap-2.5 shrink-0">
            <div>
              <label className="text-xs font-semibold text-foreground block mb-1">
                Vùng ô (Excel Range):
              </label>
              <input
                type="text"
                value={rangeStr}
                onChange={(e) => setRangeStr(e.target.value.toUpperCase())}
                placeholder="VD: A1:T30"
                className="bg-background border border-border-strong rounded-lg px-3 py-1.5 text-xs font-mono font-bold text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 w-36 uppercase"
              />
            </div>

            <Button
              type="submit"
              variant="outline"
              size="sm"
              isLoading={isLoading}
              icon={<RefreshCw className="w-3.5 h-3.5" />}
            >
              Áp dụng
            </Button>
          </form>
        </div>

        {/* Quick Range Presets */}
        <div className="flex items-center flex-wrap gap-2 pt-2 border-t border-border text-xs">
          <span className="text-muted text-[11px]">Vùng nhanh:</span>
          {[
            { label: "Toàn bộ báo cáo (A1:T32)", range: "A1:T32" },
            { label: "Bảng nhân sự FT (A3:T20)", range: "A3:T20" },
            { label: "WO Quá hạn (A10:F25)", range: "A10:F25" },
            { label: "WO Chưa quá hạn (A16:F30)", range: "A16:F30" }
          ].map((preset) => (
            <button
              key={preset.range}
              onClick={() => {
                setRangeStr(preset.range);
                loadRangeData(filePath, selectedSheet, preset.range);
              }}
              className="px-2.5 py-1 rounded-md bg-secondary text-foreground text-[11px] hover:bg-border transition-colors cursor-pointer"
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      {/* Action Bar for Copying */}
      <div className="bg-surface border border-border rounded-2xl p-4 shadow-xs flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-success" />
          <span className="text-xs font-semibold text-foreground">
            Đã sẵn sàng sao chép: Sheet <strong className="text-primary">{selectedSheet}</strong> ({previewData?.total_rows || 0} hàng × {previewData?.total_cols || 0} cột)
          </span>
        </div>

        <div className="flex items-center flex-wrap gap-2">
          <Button
            size="sm"
            onClick={() => handleCopyMode("html")}
            icon={copiedMode === "html" ? <Check className="w-4 h-4 text-success" /> : <TableIcon className="w-4 h-4" />}
          >
            {copiedMode === "html" ? "Đã copy HTML" : "Copy bảng có định dạng (HTML)"}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => handleCopyMode("image")}
            icon={copiedMode === "image" ? <Check className="w-4 h-4 text-success" /> : <ImageIcon className="w-4 h-4 text-blue-500" />}
          >
            {copiedMode === "image" ? "Đã copy ảnh" : "Copy dạng ảnh (PNG sắc nét)"}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => handleCopyMode("tsv")}
            icon={copiedMode === "tsv" ? <Check className="w-4 h-4 text-success" /> : <FileSpreadsheet className="w-4 h-4 text-emerald-500" />}
          >
            {copiedMode === "tsv" ? "Đã copy TSV" : "Copy cho Excel (TSV)"}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => handleCopyMode("text")}
            icon={copiedMode === "text" ? <Check className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4 text-amber-500" />}
          >
            {copiedMode === "text" ? "Đã copy Text" : "Copy văn bản thuần"}
          </Button>
        </div>
      </div>

      {/* Live Table Preview */}
      <Card
        header={
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2">
              <TableIcon className="w-4 h-4 text-primary" />
              <h3 className="text-sm font-bold text-foreground">
                Xem trước Bảng tính Excel — {selectedSheet} ({previewData?.range_str || rangeStr})
              </h3>
            </div>
            <span className="text-xs text-muted">
              Định dạng trực quan khớp 100% tệp gốc
            </span>
          </div>
        }
        noPadding
      >
        <div ref={previewTableRef} className="overflow-x-auto max-h-[600px] p-4 bg-background">
          {previewData && previewData.preview_rows && previewData.preview_rows.length > 0 ? (
            <table className="w-full text-xs border-collapse select-text bg-surface shadow-xs">
              <tbody>
                {previewData.preview_rows.map((row: any[], rIdx: number) => (
                  <tr key={rIdx}>
                    {row.map((cell: any, cIdx: number) => {
                      if (cell.is_slave) return null;
                      const style: React.CSSProperties = {
                        border: "1px solid #d1d5db",
                        padding: "6px 8px",
                        textAlign: cell.align || "left",
                        fontWeight: cell.bold ? "bold" : "normal"
                      };
                      if (cell.bg) style.backgroundColor = cell.bg;
                      if (cell.color) style.color = cell.color;

                      return (
                        <td
                          key={cIdx}
                          rowSpan={cell.rowspan > 1 ? cell.rowspan : undefined}
                          colSpan={cell.colspan > 1 ? cell.colspan : undefined}
                          style={style}
                          className="truncate max-w-xs"
                          title={cell.val}
                        >
                          {cell.val}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="py-16 text-center text-muted text-xs">
              {isLoading ? "Đang phân tích vùng ô..." : "Không có dữ liệu trong vùng ô đã chọn."}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};
