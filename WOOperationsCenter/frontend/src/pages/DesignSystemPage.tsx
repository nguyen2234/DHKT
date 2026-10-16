import React, { useState } from "react";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { KpiCard } from "../components/ui/KpiCard";
import { Modal } from "../components/ui/Modal";
import { useAppStore } from "../stores/appStore";
import {
  Palette,
  Check,
  AlertTriangle,
  Clock,
  Send,
  Download,
  Trash2,
  Copy,
  Info
} from "lucide-react";

export const DesignSystemPage: React.FC = () => {
  const { theme, toggleTheme, addToast } = useAppStore();
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Palette className="w-6 h-6 text-primary" />
            <span>Thư viện Thiết kế &amp; Design Tokens</span>
          </h1>
          <p className="text-xs text-muted mt-1">
            Bộ thành phần giao diện phẳng hiện đại, tuân thủ tiêu chuẩn evondevKit UI/UX cho ứng dụng doanh nghiệp.
          </p>
        </div>

        <Button variant="outline" size="sm" onClick={toggleTheme}>
          Chuyển Theme: {theme === "light" ? "Sáng" : "Tối"}
        </Button>
      </div>

      {/* 1. Viettel Red Brand Color Palette Tokens */}
      <Card
        header={
          <h3 className="text-sm font-semibold text-foreground">1. Bảng màu Nhận diện Viettel Enterprise (Design Tokens)</h3>
        }
      >
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 text-xs">
          <div className="p-3 rounded-lg border border-border bg-surface">
            <div className="h-10 rounded-md bg-primary mb-2 shadow-xs flex items-center justify-center text-white font-bold text-xs">#EE0033</div>
            <div className="font-semibold text-foreground">Viettel Primary</div>
            <div className="text-muted text-[11px]">var(--primary)</div>
          </div>

          <div className="p-3 rounded-lg border border-border bg-surface">
            <div className="h-10 rounded-md bg-[#FFF0F3] border border-primary/20 mb-2 flex items-center justify-center text-primary font-bold text-xs">#FFF0F3</div>
            <div className="font-semibold text-foreground">Primary Subtle</div>
            <div className="text-muted text-[11px]">var(--primary-subtle)</div>
          </div>

          <div className="p-3 rounded-lg border border-border bg-surface">
            <div className="h-10 rounded-md bg-background border border-border mb-2 flex items-center justify-center text-muted font-mono text-[10px]">#F7F8FA</div>
            <div className="font-semibold text-foreground">Background Canvas</div>
            <div className="text-muted text-[11px]">var(--background)</div>
          </div>

          <div className="p-3 rounded-lg border border-border bg-surface">
            <div className="h-10 rounded-md bg-surface border border-border-strong mb-2 flex items-center justify-center text-muted font-mono text-[10px]">#FFFFFF</div>
            <div className="font-semibold text-foreground">Surface Card</div>
            <div className="text-muted text-[11px]">var(--surface)</div>
          </div>

          <div className="p-3 rounded-lg border border-border bg-surface">
            <div className="h-10 rounded-md bg-success mb-2 flex items-center justify-center text-white font-bold text-xs">#10B981</div>
            <div className="font-semibold text-success">Success Progress</div>
            <div className="text-muted text-[11px]">var(--success)</div>
          </div>

          <div className="p-3 rounded-lg border border-border bg-surface">
            <div className="h-10 rounded-md bg-warning mb-2 flex items-center justify-center text-white font-bold text-xs">#F59E0B</div>
            <div className="font-semibold text-warning">Warning 30N</div>
            <div className="text-muted text-[11px]">var(--warning)</div>
          </div>
        </div>
      </Card>

      {/* 2. Button Components */}
      <Card
        header={
          <h3 className="text-sm font-semibold text-foreground">2. Các Biến thể Nút bấm (Button)</h3>
        }
      >
        <div className="space-y-4">
          <div className="flex items-center gap-3 flex-wrap">
            <Button variant="primary">Primary Button</Button>
            <Button variant="secondary">Secondary Button</Button>
            <Button variant="outline">Outline Button</Button>
            <Button variant="danger" icon={<Trash2 className="w-4 h-4" />}>
              Danger Action
            </Button>
            <Button variant="ghost">Ghost Button</Button>
          </div>

          <div className="flex items-center gap-3 pt-3 border-t border-border flex-wrap">
            <Button size="sm">Small (sm)</Button>
            <Button size="md">Medium (md)</Button>
            <Button size="lg">Large (lg)</Button>
            <Button isLoading>Đang lưu...</Button>
          </div>
        </div>
      </Card>

      {/* 3. Status Badges */}
      <Card
        header={
          <h3 className="text-sm font-semibold text-foreground">3. Huy hiệu Trạng thái (Badges)</h3>
        }
      >
        <div className="flex items-center gap-3 flex-wrap">
          <Badge variant="success" dot>Hoàn thành</Badge>
          <Badge variant="danger" dot>Quá hạn</Badge>
          <Badge variant="warning" dot>Cần lưu ý</Badge>
          <Badge variant="info" dot>Đang xử lý</Badge>
          <Badge variant="neutral">Chờ duyệt</Badge>
          <Badge variant="primary">Ưu tiên</Badge>
        </div>
      </Card>

      {/* 4. KPI Cards Preview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KpiCard
          title="Tổng tồn WO"
          value="1,008 WO"
          subtitle="Số liệu thực tế"
          variant="default"
          icon={<Clock className="w-4 h-4" />}
          onClick={() => addToast({ type: "info", message: "Bấm vào KPI card để mở chi tiết" })}
        />
        <KpiCard
          title="Tồn quá hạn"
          value="178 WO"
          subtitle="Tỷ lệ 17.6%"
          variant="danger"
          icon={<AlertTriangle className="w-4 h-4" />}
        />
        <KpiCard
          title="Thực hiện ngày"
          value="31 WO"
          subtitle="Đã hoàn thành"
          variant="success"
          icon={<Check className="w-4 h-4" />}
        />
      </div>

      {/* 5. Modals & Overlays */}
      <Card
        header={
          <h3 className="text-sm font-semibold text-foreground">5. Modal &amp; Hộp thoại</h3>
        }
      >
        <Button onClick={() => setModalOpen(true)}>Mở Modal xem thử</Button>

        <Modal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          title="Hộp thoại Mẫu của Design System"
          description="Tiêu đề phụ và hướng dẫn thao tác"
          footer={
            <>
              <Button variant="outline" size="sm" onClick={() => setModalOpen(false)}>
                Hủy bỏ
              </Button>
              <Button size="sm" onClick={() => setModalOpen(false)}>
                Xác nhận
              </Button>
            </>
          }
        >
          <div className="text-xs text-foreground space-y-2">
            <p>
              Đây là thành phần modal tiêu chuẩn, hỗ trợ bấm phím <kbd className="bg-background px-1 py-0.5 rounded border border-border">Esc</kbd> để đóng, tự động canh giữa và hỗ trợ cuộn nội dung khi quá dài.
            </p>
          </div>
        </Modal>
      </Card>
    </div>
  );
};
