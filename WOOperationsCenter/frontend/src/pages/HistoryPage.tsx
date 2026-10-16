import React, { useState, useEffect } from "react";
import { bridge, ReportHistoryItem } from "../services/bridge";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { useAppStore } from "../stores/appStore";
import {
  History,
  FileSpreadsheet,
  FileText,
  Trash2,
  Calendar,
  ExternalLink,
  Search,
  CheckCircle2,
  AlertCircle
} from "lucide-react";

export const HistoryPage: React.FC = () => {
  const { addToast } = useAppStore();
  const [historyList, setHistoryList] = useState<ReportHistoryItem[]>([]);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadHistory();
  }, [typeFilter]);

  const loadHistory = async () => {
    setIsLoading(true);
    try {
      const items = await bridge.getReportHistory(100, 0, typeFilter);
      setHistoryList(items);
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      const ok = await bridge.deleteReportHistory(id);
      if (ok) {
        setHistoryList((prev) => prev.filter((item) => item.id !== id));
        addToast({ type: "info", message: "Đã xóa bản ghi lịch sử" });
      }
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi xóa lịch sử", message: err.message });
    }
  };

  const filteredHistory = historyList.filter((item) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      item.output_path.toLowerCase().includes(q) ||
      item.report_type.toLowerCase().includes(q) ||
      item.center_selection.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Lịch sử Xuất Báo cáo
          </h1>
          <p className="text-xs text-muted mt-1">
            Lưu vết siêu dữ liệu các lần xuất báo cáo trong cơ sở dữ liệu cục bộ SQLite.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-muted absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Tìm theo tên file, loại, huyện..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-surface border border-border-strong rounded-lg pl-9 pr-3 py-1.5 text-xs text-foreground focus:outline-none w-56"
            />
          </div>

          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-surface border border-border-strong rounded-lg px-2.5 py-1.5 text-xs text-foreground focus:outline-none"
          >
            <option value="">Tất cả loại</option>
            <option value="executive_wo">Báo cáo điều hành WO</option>
            <option value="thft">Báo cáo nhân viên FT</option>
          </select>
        </div>
      </div>

      <Card noPadding>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse select-text">
            <thead className="bg-background border-b border-border text-muted font-semibold uppercase text-[11px]">
              <tr>
                <th className="py-2.5 px-4">Thời điểm xuất</th>
                <th className="py-2.5 px-4">Loại báo cáo</th>
                <th className="py-2.5 px-4">Ngày báo cáo</th>
                <th className="py-2.5 px-4">Phạm vi huyện</th>
                <th className="py-2.5 px-4">Bộ lọc</th>
                <th className="py-2.5 px-4">Đường dẫn tệp kết quả</th>
                <th className="py-2.5 px-4 text-center">Trạng thái</th>
                <th className="py-2.5 px-4 text-center">Xóa</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {isLoading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-muted">
                    Đang nạp lịch sử...
                  </td>
                </tr>
              ) : filteredHistory.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-muted">
                    Chưa có lịch sử xuất báo cáo nào được ghi nhận.
                  </td>
                </tr>
              ) : (
                filteredHistory.map((item) => (
                  <tr key={item.id} className="hover:bg-item-hover transition-colors">
                    <td className="py-2.5 px-4 font-mono text-muted">
                      {new Date(item.timestamp).toLocaleString("vi-VN")}
                    </td>
                    <td className="py-2.5 px-4 font-semibold text-foreground">
                      {item.report_type === "executive_wo" ? (
                        <span className="flex items-center gap-1.5 text-primary">
                          <FileText className="w-3.5 h-3.5" /> Điều hành WO
                        </span>
                      ) : (
                        <span className="flex items-center gap-1.5 text-info">
                          <FileSpreadsheet className="w-3.5 h-3.5" /> Báo cáo FT
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-4 text-foreground font-medium">{item.report_date}</td>
                    <td className="py-2.5 px-4 text-muted">{item.center_selection}</td>
                    <td className="py-2.5 px-4 text-muted">{item.applied_filters || "—"}</td>
                    <td className="py-2.5 px-4 font-mono text-[11px] text-foreground max-w-xs truncate" title={item.output_path}>
                      {item.output_path}
                    </td>
                    <td className="py-2.5 px-4 text-center">
                      <Badge variant="success" size="sm">
                        Thành công
                      </Badge>
                    </td>
                    <td className="py-2.5 px-4 text-center">
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="text-muted hover:text-danger p-1 rounded transition-colors cursor-pointer"
                        title="Xóa mục này"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
