import React, { useState } from "react";
import { useAppStore } from "../stores/appStore";
import { bridge } from "../services/bridge";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { CopyModeModal } from "../components/modals/CopyModeModal";
import {
  FileSpreadsheet,
  Download,
  FolderOpen,
  Check,
  Copy,
  ExternalLink,
  Layers,
  Filter,
  CheckSquare,
  Square,
  ArrowRight,
  Eye,
  FileCheck
} from "lucide-react";

export const BatchReportPage: React.FC = () => {
  const { dataset, setSelectedCenterCode, setCurrentRoute, addToast } = useAppStore();

  const allCodes = dataset?.centers.map((c) => c.code) || [];
  const [selectedCodes, setSelectedCodes] = useState<string[]>(allCodes);
  const [positionFilter, setPositionFilter] = useState<"Tất cả" | "NV DM" | "NV NHÀ TRẠM">("Tất cả");
  const [exportMode, setExportMode] = useState<"single_workbook" | "separate_workbooks">("single_workbook");
  const [outputDir, setOutputDir] = useState<string>("C:\\Reports");
  const [rememberDir, setRememberDir] = useState<boolean>(true);
  const [isExporting, setIsExporting] = useState<boolean>(false);

  // Results list after batch export
  const [exportedResults, setExportedResults] = useState<{
    paths: string[];
    exportedAt: string;
    centersCount: number;
    posFilter: string;
  } | null>(null);

  // Copy modal state
  const [copyCenterCode, setCopyCenterCode] = useState<string | null>(null);

  const handleSelectAll = () => setSelectedCodes(allCodes);
  const handleDeselectAll = () => setSelectedCodes([]);

  const handleToggleCode = (code: string) => {
    setSelectedCodes((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    );
  };

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

  const handleExecuteBatchExport = async () => {
    if (selectedCodes.length === 0) {
      addToast({ type: "warning", message: "Vui lòng chọn ít nhất một trung tâm huyện." });
      return;
    }
    if (!outputDir || !outputDir.trim()) {
      addToast({ type: "warning", message: "Vui lòng chọn thư mục lưu báo cáo." });
      return;
    }

    setIsExporting(true);
    setExportedResults(null);

    try {
      const res = await bridge.exportReport("thft_excel", {
        output_dir: outputDir,
        selected_centers: selectedCodes,
        separate_files: exportMode === "separate_workbooks",
        position_filter: positionFilter,
        remember_dir: rememberDir
      });

      if (res.success && (res.output_paths || res.output_path)) {
        const finalPaths = res.output_paths || [res.output_path!];
        setExportedResults({
          paths: finalPaths,
          exportedAt: new Date().toLocaleTimeString("vi-VN"),
          centersCount: selectedCodes.length,
          posFilter: positionFilter
        });

        addToast({
          type: "success",
          title: "Xuất hàng loạt thành công",
          message: `Đã tạo ${finalPaths.length} tệp báo cáo Excel cho ${selectedCodes.length} huyện.`
        });
      } else {
        throw new Error(res.error || "Không thể xuất file");
      }
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi xuất hàng loạt", message: err.message });
    } finally {
      setIsExporting(false);
    }
  };

  if (!dataset) {
    return (
      <div className="py-16 text-center max-w-md mx-auto">
        <FileSpreadsheet className="w-12 h-12 text-muted mx-auto mb-3" />
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
      <div className="bg-surface border border-border rounded-2xl p-5 shadow-xs space-y-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-bold text-primary uppercase tracking-wider">
              Viettel Operations — NAN_DHKT
            </span>
          </div>
          <h1 className="text-xl md:text-2xl font-bold tracking-tight text-foreground">
            Báo cáo Hàng loạt cho 14 Huyện (Batch Report)
          </h1>
          <p className="text-xs text-muted mt-1">
            Tự động tạo báo cáo cho toàn bộ hoặc nhóm huyện được chọn, hỗ trợ gom 1 workbook nhiều sheet hoặc tách riêng từng huyện.
          </p>
        </div>
      </div>

      {/* Configuration Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* District Selection Column (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <Card
            header={
              <div className="flex items-center justify-between w-full">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-foreground">
                    Chọn các Trung tâm Huyện ({selectedCodes.length}/{allCodes.length})
                  </h3>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleSelectAll}
                    className="text-xs text-primary font-semibold hover:underline cursor-pointer"
                  >
                    Chọn tất cả
                  </button>
                  <span className="text-muted text-xs">•</span>
                  <button
                    onClick={handleDeselectAll}
                    className="text-xs text-muted hover:text-foreground cursor-pointer"
                  >
                    Bỏ chọn
                  </button>
                </div>
              </div>
            }
            noPadding
          >
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 p-4">
              {dataset.centers.map((c) => {
                const isSelected = selectedCodes.includes(c.code);
                return (
                  <div
                    key={c.code}
                    onClick={() => handleToggleCode(c.code)}
                    className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center justify-between gap-2 ${
                      isSelected
                        ? "bg-primary-subtle border-primary text-foreground"
                        : "bg-background border-border text-muted hover:text-foreground hover:border-border-strong"
                    }`}
                  >
                    <div className="min-w-0">
                      <div className="font-bold text-xs flex items-center gap-1.5">
                        <span className={`px-1.5 py-0.2 rounded text-[10px] ${
                          isSelected ? "bg-primary text-primary-foreground font-bold" : "bg-secondary text-muted"
                        }`}>
                          {c.code}
                        </span>
                        <span className="truncate">{c.name}</span>
                      </div>
                      <div className="text-[11px] text-muted mt-1">
                        {c.total_employees} FT • <span className="text-danger font-semibold">{c.tagged_employees} Tag</span>
                      </div>
                    </div>
                    {isSelected ? (
                      <CheckSquare className="w-4 h-4 text-primary shrink-0" />
                    ) : (
                      <Square className="w-4 h-4 text-muted shrink-0" />
                    )}
                  </div>
                );
              })}
            </div>
          </Card>
        </div>

        {/* Options & Export Column (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <Card
            header={
              <h3 className="text-sm font-semibold text-foreground">
                Cấu hình Chế độ Xuất & Thư mục
              </h3>
            }
          >
            <div className="space-y-4 text-xs">
              {/* Position Filter */}
              <div>
                <label className="font-semibold text-foreground block mb-1.5">
                  Lọc chức danh nhân sự:
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {(["Tất cả", "NV DM", "NV NHÀ TRẠM"] as const).map((filter) => (
                    <button
                      key={filter}
                      type="button"
                      onClick={() => setPositionFilter(filter)}
                      className={`py-2 px-2 rounded-lg font-semibold text-center transition-all cursor-pointer ${
                        positionFilter === filter
                          ? "bg-primary text-primary-foreground shadow-xs"
                          : "bg-background border border-border text-muted hover:text-foreground"
                      }`}
                    >
                      {filter}
                    </button>
                  ))}
                </div>
              </div>

              {/* Export Mode */}
              <div>
                <label className="font-semibold text-foreground block mb-1.5">
                  Quy cách tệp Excel đầu ra:
                </label>
                <div className="space-y-2">
                  <label className="flex items-start gap-2.5 p-3 rounded-xl border border-border bg-background cursor-pointer">
                    <input
                      type="radio"
                      name="export_mode"
                      checked={exportMode === "single_workbook"}
                      onChange={() => setExportMode("single_workbook")}
                      className="accent-primary mt-0.5"
                    />
                    <div>
                      <div className="font-semibold text-foreground">Một Workbook nhiều Sheet (Khuyên dùng)</div>
                      <div className="text-[11px] text-muted mt-0.5">
                        Tất cả các huyện được lưu trong 1 file Excel duy nhất, mỗi huyện 1 worksheet riêng biệt.
                      </div>
                    </div>
                  </label>

                  <label className="flex items-start gap-2.5 p-3 rounded-xl border border-border bg-background cursor-pointer">
                    <input
                      type="radio"
                      name="export_mode"
                      checked={exportMode === "separate_workbooks"}
                      onChange={() => setExportMode("separate_workbooks")}
                      className="accent-primary mt-0.5"
                    />
                    <div>
                      <div className="font-semibold text-foreground">Mỗi huyện một Workbook riêng</div>
                      <div className="text-[11px] text-muted mt-0.5">
                        Xuất thành các file riêng biệt (ví dụ: BaoCao_THFT_DCU_20261015.xlsx).
                      </div>
                    </div>
                  </label>
                </div>
              </div>

              {/* Directory Picker */}
              <div>
                <label className="font-semibold text-foreground block mb-1">
                  Thư mục lưu báo cáo:
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={outputDir}
                    onChange={(e) => setOutputDir(e.target.value)}
                    className="flex-1 bg-background border border-border-strong rounded-lg px-3 py-1.5 text-foreground focus:outline-none"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handlePickDirectory}
                    icon={<FolderOpen className="w-3.5 h-3.5 text-primary" />}
                  >
                    Chọn...
                  </Button>
                </div>
              </div>

              <label className="flex items-center gap-2 cursor-pointer pt-1">
                <input
                  type="checkbox"
                  checked={rememberDir}
                  onChange={(e) => setRememberDir(e.target.checked)}
                  className="rounded text-primary accent-primary w-3.5 h-3.5"
                />
                <span className="text-muted text-[11px]">Ghi nhớ thư mục lưu mặc định</span>
              </label>

              {/* Execute Button */}
              <div className="pt-2">
                <Button
                  className="w-full justify-center"
                  size="md"
                  onClick={handleExecuteBatchExport}
                  isLoading={isExporting}
                  icon={<Download className="w-4 h-4" />}
                >
                  {isExporting
                    ? "Đang xuất báo cáo hàng loạt..."
                    : `Bắt đầu xuất cho ${selectedCodes.length} huyện`}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Results Section */}
      {exportedResults && (
        <Card
          header={
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-2">
                <FileCheck className="w-4 h-4 text-success" />
                <h3 className="text-sm font-bold text-foreground">
                  Kết quả Xuất Báo cáo Hàng loạt ({exportedResults.paths.length} file)
                </h3>
              </div>
              <span className="text-xs text-muted">Hoàn tất lúc {exportedResults.exportedAt}</span>
            </div>
          }
          noPadding
        >
          <div className="divide-y divide-border text-xs">
            {exportedResults.paths.map((p, idx) => (
              <div key={p + idx} className="p-3.5 flex items-center justify-between flex-wrap gap-3 hover:bg-item-hover">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-8 h-8 rounded-lg bg-success-bg text-success flex items-center justify-center font-bold shrink-0">
                    <FileSpreadsheet className="w-4 h-4" />
                  </div>
                  <div className="min-w-0">
                    <div className="font-mono text-xs font-semibold text-foreground truncate">{p}</div>
                    <div className="text-[11px] text-muted">
                      Bộ lọc: <span className="font-medium text-foreground">{exportedResults.posFilter}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => bridge.openFile(p)}
                    icon={<ExternalLink className="w-3.5 h-3.5" />}
                  >
                    Mở tệp
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => bridge.openFolder(p)}
                    icon={<FolderOpen className="w-3.5 h-3.5" />}
                  >
                    Thư mục
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};
