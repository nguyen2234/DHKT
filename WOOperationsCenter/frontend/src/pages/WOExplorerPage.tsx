import React, { useState, useEffect } from "react";
import { useAppStore } from "../stores/appStore";
import { bridge, WorkOrderItem } from "../services/bridge";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Modal } from "../components/ui/Modal";
import {
  Briefcase,
  Search,
  Filter,
  ArrowUpDown,
  Copy,
  Download,
  AlertTriangle,
  Clock,
  HelpCircle,
  Eye,
  Check,
  ChevronLeft,
  ChevronRight
} from "lucide-react";

export const WOExplorerPage: React.FC = () => {
  const { dataset, addToast, setCurrentRoute } = useAppStore();

  const [searchQuery, setSearchQuery] = useState("");
  const [classification, setClassification] = useState<string>("all");
  const [selectedCenter, setSelectedCenter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [sortBy, setSortBy] = useState<string>("overdue_days");
  const [sortOrder, setSortOrder] = useState<string>("asc");
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(50);

  const [items, setItems] = useState<WorkOrderItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const [selectedWo, setSelectedWo] = useState<WorkOrderItem | null>(null);
  const [isCopied, setIsCopied] = useState<boolean>(false);

  useEffect(() => {
    if (dataset) {
      loadWorkOrders();
    }
  }, [dataset, classification, selectedCenter, statusFilter, sortBy, sortOrder, page, pageSize]);

  const loadWorkOrders = async () => {
    if (!dataset) return;
    setIsLoading(true);
    try {
      const res = await bridge.queryWorkOrders({
        search_query: searchQuery,
        classification: classification === "all" ? undefined : classification,
        center_code: selectedCenter || undefined,
        status: statusFilter || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
        page,
        page_size: pageSize
      });
      setItems(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi truy vấn WO", message: err.message });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadWorkOrders();
  };

  const handleCopyTsv = async () => {
    if (items.length === 0) return;
    const headers = [
      "Mã WO",
      "Loại công việc",
      "Nội dung",
      "Thời hạn",
      "Trạng thái",
      "Nhân viên",
      "Mã trạm",
      "Ngày quá hạn",
      "Huyện"
    ];
    const rows = items.map((w) =>
      [
        w.code,
        w.job_type,
        w.content,
        w.deadline,
        w.status,
        w.performer,
        w.station_code,
        w.overdue_days,
        w.center_code
      ].join("\t")
    );
    const tsv = [headers.join("\t"), ...rows].join("\n");
    await bridge.copyToClipboard("text", { text: tsv });
    setIsCopied(true);
    addToast({
      type: "success",
      title: "Đã copy danh sách",
      message: `Đã copy ${items.length} dòng dạng bảng TSV vào Clipboard.`
    });
    setTimeout(() => setIsCopied(false), 2500);
  };

  if (!dataset) {
    return (
      <div className="py-16 text-center max-w-md mx-auto">
        <Briefcase className="w-12 h-12 text-muted mx-auto mb-3" />
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
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Danh sách Công việc WO (Module C)
          </h1>
          <p className="text-xs text-muted mt-1">
            Tra cứu, phân loại chi tiết {dataset.total_work_orders + dataset.total_pending_work_orders + dataset.total_boundary_work_orders} công việc từ sheet <span className="font-semibold text-foreground">WO</span>
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={handleCopyTsv}
            icon={isCopied ? <Check className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
          >
            {isCopied ? "Đã copy TSV" : "Copy trang hiện tại"}
          </Button>
        </div>
      </div>

      {/* Classification Filters Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
        <button
          onClick={() => {
            setClassification("all");
            setPage(1);
          }}
          className={`p-3.5 rounded-xl border text-left transition-colors cursor-pointer ${
            classification === "all"
              ? "bg-surface border-primary ring-1 ring-primary shadow-xs"
              : "bg-surface border-border hover:border-foreground/30"
          }`}
        >
          <div className="text-muted font-medium">Tất cả công việc</div>
          <div className="text-lg font-bold text-foreground mt-1">
            {dataset.total_work_orders + dataset.total_pending_work_orders + dataset.total_boundary_work_orders} WO
          </div>
        </button>

        <button
          onClick={() => {
            setClassification("overdue");
            setPage(1);
          }}
          className={`p-3.5 rounded-xl border text-left transition-colors cursor-pointer ${
            classification === "overdue"
              ? "bg-surface border-danger ring-1 ring-danger shadow-xs"
              : "bg-surface border-border hover:border-danger/30"
          }`}
        >
          <div className="text-danger font-medium flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5" /> Quá hạn (Cột L &lt; 0)
          </div>
          <div className="text-lg font-bold text-danger mt-1">{dataset.total_work_orders} WO</div>
        </button>

        <button
          onClick={() => {
            setClassification("pending");
            setPage(1);
          }}
          className={`p-3.5 rounded-xl border text-left transition-colors cursor-pointer ${
            classification === "pending"
              ? "bg-surface border-success ring-1 ring-success shadow-xs"
              : "bg-surface border-border hover:border-success/30"
          }`}
        >
          <div className="text-success font-medium flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" /> Tồn trong hạn (Cột L &gt; 0)
          </div>
          <div className="text-lg font-bold text-success mt-1">
            {dataset.total_pending_work_orders} WO
          </div>
        </button>

        <button
          onClick={() => {
            setClassification("boundary");
            setPage(1);
          }}
          className={`p-3.5 rounded-xl border text-left transition-colors cursor-pointer ${
            classification === "boundary"
              ? "bg-surface border-neutral ring-1 ring-neutral shadow-xs"
              : "bg-surface border-border hover:border-foreground/30"
          }`}
        >
          <div className="text-muted font-medium flex items-center gap-1.5">
            <HelpCircle className="w-3.5 h-3.5" /> Biên / Chưa xác định
          </div>
          <div className="text-lg font-bold text-foreground mt-1">
            {dataset.total_boundary_work_orders} WO
          </div>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <Card noPadding>
        <form onSubmit={handleSearchSubmit} className="p-3.5 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-3 flex-1 min-w-[280px]">
            <div className="relative flex-1">
              <Search className="w-3.5 h-3.5 text-muted absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Tìm mã WO, nhân viên, trạm, nội dung..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-background border border-border-strong rounded-lg pl-9 pr-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
              />
            </div>
            <Button type="submit" size="sm">
              Tìm kiếm
            </Button>
          </div>

          <div className="flex items-center gap-2.5 flex-wrap">
            {/* Center Filter */}
            <select
              value={selectedCenter}
              onChange={(e) => {
                setSelectedCenter(e.target.value);
                setPage(1);
              }}
              className="bg-background border border-border-strong rounded-lg px-2.5 py-2 text-foreground focus:outline-none"
            >
              <option value="">Tất cả huyện</option>
              {dataset.centers.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.code} - {c.name}
                </option>
              ))}
            </select>

            {/* Sort Order */}
            <select
              value={`${sortBy}_${sortOrder}`}
              onChange={(e) => {
                const [b, o] = e.target.value.split("_");
                setSortBy(b);
                setSortOrder(o);
                setPage(1);
              }}
              className="bg-background border border-border-strong rounded-lg px-2.5 py-2 text-foreground focus:outline-none"
            >
              <option value="overdue_days_asc">Số ngày: Tăng dần (Quá hạn trước)</option>
              <option value="overdue_days_desc">Số ngày: Giảm dần</option>
              <option value="code_asc">Mã WO (A &rarr; Z)</option>
              <option value="performer_asc">Nhân viên thực hiện</option>
              <option value="deadline_desc">Hạn kết thúc gần nhất</option>
            </select>
          </div>
        </form>
      </Card>

      {/* Main WO Table */}
      <Card noPadding>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse select-text">
            <thead className="bg-background border-b border-border text-muted font-semibold uppercase text-[11px] sticky top-0">
              <tr>
                <th className="py-2.5 px-3">STT</th>
                <th className="py-2.5 px-3">Mã công việc</th>
                <th className="py-2.5 px-3">Loại công việc</th>
                <th className="py-2.5 px-3">Nội dung</th>
                <th className="py-2.5 px-3">Hạn kết thúc</th>
                <th className="py-2.5 px-3">Trạng thái</th>
                <th className="py-2.5 px-3">Nhân viên</th>
                <th className="py-2.5 px-3">Mã trạm</th>
                <th className="py-2.5 px-3 text-center">Ngày quá hạn</th>
                <th className="py-2.5 px-3 text-center">Huyện</th>
                <th className="py-2.5 px-3 text-center">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {isLoading ? (
                <tr>
                  <td colSpan={11} className="py-12 text-center text-muted">
                    Đang nạp dữ liệu...
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={11} className="py-12 text-center text-muted">
                    Không tìm thấy công việc phù hợp với tiêu chí lọc.
                  </td>
                </tr>
              ) : (
                items.map((wo, idx) => (
                  <tr key={wo.code + idx} className="hover:bg-item-hover transition-colors">
                    <td className="py-2.5 px-3 text-muted">{wo.stt}</td>
                    <td className="py-2.5 px-3 font-mono font-medium text-foreground">{wo.code}</td>
                    <td className="py-2.5 px-3 text-muted">{wo.job_type}</td>
                    <td className="py-2.5 px-3 max-w-xs truncate text-foreground" title={wo.content}>
                      {wo.content}
                    </td>
                    <td className="py-2.5 px-3 text-muted">{wo.deadline}</td>
                    <td className="py-2.5 px-3">
                      <span className="truncate max-w-[120px] inline-block">{wo.status}</span>
                    </td>
                    <td className="py-2.5 px-3 font-medium text-foreground">{wo.performer}</td>
                    <td className="py-2.5 px-3 font-mono text-muted">{wo.station_code}</td>
                    <td className="py-2.5 px-3 text-center">
                      {wo.classification === "overdue" ? (
                        <span className="font-bold text-danger">{wo.overdue_days} ngày</span>
                      ) : wo.classification === "pending" ? (
                        <span className="font-bold text-success">+{wo.overdue_days} ngày</span>
                      ) : (
                        <span className="text-muted">{wo.overdue_days ?? "—"}</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-center font-bold text-foreground">
                      {wo.center_code}
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <button
                        onClick={() => setSelectedWo(wo)}
                        className="text-primary hover:underline font-medium p-1 cursor-pointer"
                        title="Xem chi tiết WO"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="p-3.5 border-t border-border bg-background/50 flex items-center justify-between text-xs text-muted">
          <div>
            Hiển thị <span className="font-semibold text-foreground">{items.length}</span> / {total} công việc
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1 || isLoading}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              icon={<ChevronLeft className="w-3.5 h-3.5" />}
            >
              Trang trước
            </Button>
            <span className="font-medium text-foreground px-2">
              Trang {page} / {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages || isLoading}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              icon={<ChevronRight className="w-3.5 h-3.5" />}
              iconPosition="right"
            >
              Trang sau
            </Button>
          </div>
        </div>
      </Card>

      {/* Work Order Detail Modal */}
      <Modal
        isOpen={selectedWo !== null}
        onClose={() => setSelectedWo(null)}
        title="Chi tiết Công việc WO"
        description={selectedWo?.code}
        size="lg"
      >
        {selectedWo && (
          <div className="space-y-4 text-xs">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-background p-3 rounded-lg">
                <span className="text-muted block mb-1">Mã công việc:</span>
                <span className="font-mono font-bold text-foreground text-sm">{selectedWo.code}</span>
              </div>
              <div className="bg-background p-3 rounded-lg">
                <span className="text-muted block mb-1">Phân loại & Trạng thái:</span>
                <div className="flex items-center gap-2">
                  <Badge variant={selectedWo.classification === "overdue" ? "danger" : "success"}>
                    {selectedWo.classification === "overdue" ? "Quá hạn" : "Tồn trong hạn"}
                  </Badge>
                  <span className="text-muted font-medium">{selectedWo.status}</span>
                </div>
              </div>
            </div>

            <div className="bg-background p-3 rounded-lg">
              <span className="text-muted block mb-1">Loại công việc:</span>
              <span className="font-medium text-foreground">{selectedWo.job_type}</span>
            </div>

            <div className="bg-background p-3 rounded-lg">
              <span className="text-muted block mb-1">Nội dung chi tiết:</span>
              <p className="text-foreground leading-relaxed select-text">{selectedWo.content}</p>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div className="bg-background p-3 rounded-lg">
                <span className="text-muted block mb-1">Nhân viên thực hiện:</span>
                <span className="font-semibold text-foreground">{selectedWo.performer}</span>
              </div>
              <div className="bg-background p-3 rounded-lg">
                <span className="text-muted block mb-1">Số điện thoại FT:</span>
                <span className="font-mono font-semibold text-foreground">{selectedWo.ft_mobile || "—"}</span>
              </div>
              <div className="bg-background p-3 rounded-lg">
                <span className="text-muted block mb-1">Mã trạm:</span>
                <span className="font-mono font-semibold text-foreground">{selectedWo.station_code}</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="bg-background p-3 rounded-lg">
                <span className="text-muted block mb-1">Thời hạn kết thúc:</span>
                <span className="font-medium text-foreground">{selectedWo.deadline}</span>
              </div>
              <div className="bg-background p-3 rounded-lg">
                <span className="text-muted block mb-1">Số ngày quá hạn / Còn lại:</span>
                <span
                  className={`font-bold text-sm ${
                    selectedWo.classification === "overdue" ? "text-danger" : "text-success"
                  }`}
                >
                  {selectedWo.overdue_days} ngày
                </span>
              </div>
            </div>

            {selectedWo.ft_comment && (
              <div className="bg-background p-3 rounded-lg">
                <span className="text-muted block mb-1">FT Comment:</span>
                <p className="text-foreground italic">{selectedWo.ft_comment}</p>
              </div>
            )}

            {selectedWo.bkk && (
              <div className="bg-background p-3 rounded-lg border border-warning/30">
                <span className="text-warning font-semibold block mb-1">Bất khả kháng (BKK):</span>
                <p className="text-foreground">{selectedWo.bkk} — {selectedWo.bkk_reason}</p>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};
