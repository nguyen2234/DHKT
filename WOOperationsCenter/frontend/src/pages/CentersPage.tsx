import React, { useState } from "react";
import { useAppStore } from "../stores/appStore";
import { CenterDetailPage } from "./CenterDetailPage";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import {
  Building2,
  Users,
  Tag,
  AlertTriangle,
  Clock,
  CheckCircle2,
  ArrowRight,
  Search,
  LayoutGrid,
  FileSpreadsheet
} from "lucide-react";

export const CentersPage: React.FC = () => {
  const { dataset, setSelectedCenterCode, setCurrentRoute } = useAppStore();
  const [viewMode, setViewMode] = useState<"workspace" | "grid">("workspace");
  const [search, setSearch] = useState("");

  if (!dataset) {
    return (
      <div className="py-16 text-center max-w-md mx-auto">
        <Building2 className="w-12 h-12 text-muted mx-auto mb-3" />
        <h3 className="text-base font-semibold text-foreground">Chưa có dữ liệu</h3>
        <p className="text-xs text-muted mt-1">Vui lòng nạp tệp Excel điều hành trước.</p>
        <div className="mt-4">
          <Button onClick={() => setCurrentRoute("import")}>Đến trang Nhập dữ liệu</Button>
        </div>
      </div>
    );
  }

  // If in workspace mode, render the CenterDetailPage workspace directly with full features
  if (viewMode === "workspace") {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="text-xs text-muted">
            Đang hiển thị không gian báo cáo chi tiết từng huyện
          </div>
          <button
            onClick={() => setViewMode("grid")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border bg-surface text-xs font-semibold text-foreground hover:bg-item-hover transition-colors cursor-pointer"
          >
            <LayoutGrid className="w-3.5 h-3.5 text-primary" />
            <span>Xem lưới tổng quan 14 huyện</span>
          </button>
        </div>
        <CenterDetailPage />
      </div>
    );
  }

  const filteredCenters = dataset.centers.filter(
    (c) =>
      c.code.toLowerCase().includes(search.toLowerCase()) ||
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.full_name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-bold text-primary uppercase tracking-wider">
              Viettel Operations — NAN_DHKT
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Danh sách 14 Trung tâm Huyện
          </h1>
          <p className="text-xs text-muted mt-1">
            Dữ liệu trích xuất theo kỳ báo cáo ngày {dataset.report_date_str}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setViewMode("workspace")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary-hover transition-colors cursor-pointer shadow-xs"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span>Vào không gian làm việc huyện</span>
          </button>

          <div className="relative">
            <Search className="w-3.5 h-3.5 text-muted absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Tìm theo mã hoặc tên huyện..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-surface border border-border-strong rounded-lg pl-9 pr-3 py-1.5 text-xs text-foreground focus:outline-none w-56"
            />
          </div>
        </div>
      </div>

      {/* Grid of Center Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredCenters.map((c) => (
          <div
            key={c.code}
            onClick={() => {
              setSelectedCenterCode(c.code);
              setViewMode("workspace");
            }}
            className="bg-surface border border-border rounded-xl p-5 hover:border-primary/40 hover:shadow-xs transition-all cursor-pointer flex flex-col justify-between group"
          >
            <div>
              {/* Card Header */}
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold text-base shrink-0">
                    {c.code}
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-foreground group-hover:text-primary transition-colors">
                      {c.name}
                    </h3>
                    <div className="text-[11px] text-muted truncate max-w-[170px]" title={c.full_name}>
                      {c.full_name}
                    </div>
                  </div>
                </div>

                <Badge variant={c.danh_gia === "Đạt" ? "success" : "danger"} size="sm">
                  {c.danh_gia || "Chưa rõ"}
                </Badge>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-border text-xs">
                <div className="bg-background p-2.5 rounded-lg">
                  <span className="text-muted block text-[11px]">Tổng tồn WO:</span>
                  <span className="font-bold text-foreground text-sm">{c.tong_ton}</span>
                </div>
                <div className="bg-background p-2.5 rounded-lg">
                  <span className="text-danger block text-[11px]">Tồn quá hạn:</span>
                  <span className="font-bold text-danger text-sm">{c.ton_qua_han}</span>
                </div>
                <div className="bg-background p-2.5 rounded-lg">
                  <span className="text-muted block text-[11px]">Tổng nhân sự FT:</span>
                  <span className="font-semibold text-foreground text-sm">{c.total_employees} FT</span>
                </div>
                <div className="bg-background p-2.5 rounded-lg">
                  <span className="text-danger block text-[11px]">Nhân viên cần TAG:</span>
                  <span className="font-bold text-danger text-sm">{c.tagged_employees} FT</span>
                </div>
              </div>

              {/* Secondary stats */}
              <div className="mt-3 flex items-center justify-between text-[11px] text-muted">
                <span>
                  Tồn &gt;30N: <b className="text-warning">{c.ton_30_ngay || "0"}</b>
                </span>
                <span>
                  TH Ngày: <b className="text-success">{c.thuc_hien_ngay}</b>
                </span>
                <span>
                  Tỷ lệ HT: <b className="text-foreground">{(c.ty_le_ht_ngay * 100).toFixed(0)}%</b>
                </span>
              </div>
            </div>

            {/* Action link */}
            <div className="mt-4 pt-3 border-t border-border flex items-center justify-between text-xs font-semibold text-primary">
              <span>Mở không gian gửi TAMMI</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
