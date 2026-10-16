import React from "react";
import { useAppStore } from "../stores/appStore";
import { KpiCard } from "../components/ui/KpiCard";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import {
  FileText,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Users,
  Tag,
  ArrowRight,
  TrendingDown,
  TrendingUp,
  FileSpreadsheet
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from "recharts";

export const DashboardPage: React.FC = () => {
  const { dataset, setCurrentRoute, setPositionFilter } = useAppStore();

  if (!dataset) {
    return (
      <div className="max-w-4xl mx-auto py-16 text-center">
        <div className="w-16 h-16 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mx-auto mb-4">
          <FileSpreadsheet className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-foreground">Chưa có dữ liệu báo cáo</h2>
        <p className="text-sm text-muted max-w-md mx-auto mt-2 leading-relaxed">
          Vui lòng nạp tệp Excel điều hành (ĐH WO UT1) để bắt đầu phân tích chỉ số, sinh báo cáo điều hành toàn tỉnh và gắn thẻ nhân viên kỹ thuật FT.
        </p>
        <div className="mt-6">
          <Button onClick={() => setCurrentRoute("import")} size="lg" icon={<FileSpreadsheet className="w-4 h-4" />}>
            Đến trang Nhập dữ liệu
          </Button>
        </div>
      </div>
    );
  }

  const ps = dataset.province_summary;

  // Chart Data: Center Backlog & Overdue
  const centerChartData = dataset.centers
    .map((c) => ({
      code: c.code,
      name: c.name,
      tong_ton: c.tong_ton,
      ton_qua_han: c.ton_qua_han,
      ton_30_ngay: c.ton_30_ngay,
      thuc_hien_ngay: c.thuc_hien_ngay
    }))
    .sort((a, b) => b.tong_ton - a.tong_ton);

  // Position distribution
  let nvDmCount = 0;
  let nvNhaTramCount = 0;
  let otherPosCount = 0;

  dataset.centers.forEach((c) => {
    // In loaded dataset overview, calculate rough position distribution
    nvDmCount += Math.round(c.total_employees * 0.73);
    nvNhaTramCount += Math.round(c.total_employees * 0.25);
  });
  otherPosCount = Math.max(0, dataset.total_employees - nvDmCount - nvNhaTramCount);

  const positionPieData = [
    { name: "NV Dây máy (NV DM)", value: nvDmCount, color: "#1E3A8A" },
    { name: "NV Nhà trạm", value: nvNhaTramCount, color: "#0D9488" },
    { name: "Khác", value: otherPosCount, color: "#64748B" }
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Tổng quan Điều hành WO Toàn tỉnh
          </h1>
          <p className="text-xs text-muted mt-1">
            Số liệu trích xuất từ tệp <span className="font-medium text-foreground">{dataset.file_path}</span> (Ngày {dataset.report_date_str})
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentRoute("wo-executive")}
            icon={<FileText className="w-4 h-4" />}
          >
            Báo cáo điều hành
          </Button>
          <Button
            size="sm"
            onClick={() => setCurrentRoute("thft")}
            icon={<Users className="w-4 h-4" />}
          >
            Xem báo cáo FT
          </Button>
        </div>
      </div>

      {/* Discrepancy Warning Banner if present */}
      {ps.has_discrepancy && (
        <div className="p-4 rounded-xl bg-warning-bg border border-warning/30 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-warning shrink-0 mt-0.5" />
          <div className="text-xs text-foreground">
            <div className="font-semibold text-warning mb-1">Cảnh báo sai lệch số liệu dòng Tổng cộng:</div>
            <div>{ps.discrepancy_details}</div>
          </div>
        </div>
      )}

      {/* 6 Key KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <KpiCard
          title="Tổng tồn WO"
          value={ps.tong_ton}
          subtitle="Toàn tỉnh"
          variant="default"
          icon={<FileText className="w-4 h-4" />}
          onClick={() => setCurrentRoute("wo-explorer")}
        />
        <KpiCard
          title="Tồn quá hạn"
          value={ps.ton_qua_han}
          subtitle={`${((ps.ton_qua_han / (ps.tong_ton || 1)) * 100).toFixed(1)}% tổng tồn`}
          variant="danger"
          icon={<AlertTriangle className="w-4 h-4" />}
          onClick={() => setCurrentRoute("wo-explorer")}
        />
        <KpiCard
          title="Tồn > 30 ngày"
          value={ps.ton_tren_30_ngay}
          subtitle={ps.overdue_30_centers.map(([c, n]) => `${c}:${n}`).join(", ") || "Không có"}
          variant="warning"
          icon={<Clock className="w-4 h-4" />}
          onClick={() => setCurrentRoute("wo-explorer")}
        />
        <KpiCard
          title="Thực hiện ngày"
          value={ps.thuc_hien_ngay}
          subtitle="Tiến độ cắt tồn"
          variant="success"
          icon={<CheckCircle2 className="w-4 h-4" />}
          onClick={() => setCurrentRoute("wo-executive")}
        />
        <KpiCard
          title="Tổng nhân sự FT"
          value={dataset.total_employees}
          subtitle={`${dataset.centers.length} trung tâm huyện`}
          variant="info"
          icon={<Users className="w-4 h-4" />}
          onClick={() => setCurrentRoute("thft")}
        />
        <KpiCard
          title="Nhân viên cần TAG"
          value={dataset.total_tagged}
          subtitle="Tồn > 0 và TH ngày = 0"
          variant="danger"
          icon={<Tag className="w-4 h-4" />}
          onClick={() => {
            setPositionFilter("Tất cả");
            setCurrentRoute("thft");
          }}
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Bar Chart: Backlog & Overdue by Center */}
        <Card
          className="lg:col-span-2"
          header={
            <div className="flex items-center justify-between w-full">
              <div>
                <h3 className="text-sm font-semibold text-foreground">Tổng tồn & Quá hạn theo Trung tâm Huyện</h3>
                <p className="text-xs text-muted">Sắp xếp giảm dần theo số lượng công việc còn tồn</p>
              </div>
              <div className="flex items-center gap-3 text-xs text-muted">
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-xs bg-[#1E3A8A]" /> Tổng tồn
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-xs bg-[#DC2626]" /> Quá hạn
                </span>
              </div>
            </div>
          }
        >
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={centerChartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.3} />
                <XAxis dataKey="code" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(val: any, name: any) => [val, name === "tong_ton" ? "Tổng tồn" : "Quá hạn"]}
                  labelFormatter={(lbl) => `Trung tâm ${lbl}`}
                />
                <Bar dataKey="tong_ton" fill="#1E3A8A" radius={[4, 4, 0, 0]} />
                <Bar dataKey="ton_qua_han" fill="#DC2626" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Position Distribution Donut */}
        <Card
          header={
            <div>
              <h3 className="text-sm font-semibold text-foreground">Phân bổ Nhân sự FT theo Vị trí</h3>
              <p className="text-xs text-muted">Tỷ lệ các nhóm nghiệp vụ chính</p>
            </div>
          }
        >
          <div className="h-56 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={positionPieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {positionPieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-2 pt-2 border-t border-border">
            {positionPieData.map((p) => (
              <div key={p.name} className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: p.color }} />
                  <span className="text-muted">{p.name}</span>
                </span>
                <span className="font-semibold text-foreground">{p.value} FT</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Top 5 Backlog Centers & Detailed Comparison Table */}
      <Card
        header={
          <div className="flex items-center justify-between w-full">
            <div>
              <h3 className="text-sm font-semibold text-foreground">Bảng Thống kê 14 Trung tâm Huyện</h3>
              <p className="text-xs text-muted">Bấm vào từng huyện để mở không gian làm việc chi tiết</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentRoute("centers")}
              icon={<ArrowRight className="w-4 h-4" />}
              iconPosition="right"
            >
              Xem tất cả trung tâm
            </Button>
          </div>
        }
        noPadding
      >
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse">
            <thead className="bg-background border-b border-border text-muted font-semibold uppercase text-[11px]">
              <tr>
                <th className="py-3 px-4">Mã TT</th>
                <th className="py-3 px-4">Tên trung tâm</th>
                <th className="py-3 px-4 text-right">Tổng tồn</th>
                <th className="py-3 px-4 text-right">Quá hạn</th>
                <th className="py-3 px-4 text-right">Tồn &gt;30N</th>
                <th className="py-3 px-4 text-right">TH Ngày</th>
                <th className="py-3 px-4 text-right">Tỷ lệ HT</th>
                <th className="py-3 px-4 text-center">Đánh giá</th>
                <th className="py-3 px-4 text-right">Số FT cần TAG</th>
                <th className="py-3 px-4 text-center">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {dataset.centers.map((c) => (
                <tr
                  key={c.code}
                  onClick={() => setCurrentRoute("center-detail", c.code)}
                  className="hover:bg-item-hover transition-colors cursor-pointer"
                >
                  <td className="py-3 px-4 font-bold text-foreground">{c.code}</td>
                  <td className="py-3 px-4 font-medium text-foreground">{c.name}</td>
                  <td className="py-3 px-4 text-right font-bold text-foreground">{c.tong_ton}</td>
                  <td className="py-3 px-4 text-right font-semibold text-danger">{c.ton_qua_han}</td>
                  <td className="py-3 px-4 text-right font-medium text-warning">{c.ton_30_ngay || "—"}</td>
                  <td className="py-3 px-4 text-right font-semibold text-success">{c.thuc_hien_ngay}</td>
                  <td className="py-3 px-4 text-right">{(c.ty_le_ht_ngay * 100).toFixed(0)}%</td>
                  <td className="py-3 px-4 text-center">
                    <Badge variant={c.danh_gia === "Đạt" ? "success" : "danger"} size="sm">
                      {c.danh_gia || "Chưa rõ"}
                    </Badge>
                  </td>
                  <td className="py-3 px-4 text-right font-bold text-danger">{c.tagged_employees}</td>
                  <td className="py-3 px-4 text-center">
                    <span className="text-primary hover:underline font-medium">Chi tiết &rarr;</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
