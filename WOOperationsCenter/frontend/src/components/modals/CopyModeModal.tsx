import React, { useState } from "react";
import { Modal } from "../ui/Modal";
import { Button } from "../ui/Button";
import { useAppStore } from "../../stores/appStore";
import {
  Table,
  Image as ImageIcon,
  FileText,
  FileSpreadsheet,
  Check,
  Copy,
  Info
} from "lucide-react";
import { ClipboardCopyMode } from "../../services/clipboardHelper";

export interface CopyModeModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  onConfirmCopy: (mode: ClipboardCopyMode) => Promise<boolean>;
}

export const CopyModeModal: React.FC<CopyModeModalProps> = ({
  isOpen,
  onClose,
  title = "Chọn định dạng sao chép cho TAMMI",
  onConfirmCopy
}) => {
  const { addToast } = useAppStore();
  const [selectedMode, setSelectedMode] = useState<ClipboardCopyMode>("html");
  const [isCopying, setIsCopying] = useState(false);

  const options: {
    mode: ClipboardCopyMode;
    label: string;
    desc: string;
    icon: React.ReactNode;
    recommended?: boolean;
  }[] = [
    {
      mode: "html",
      label: "Copy bảng có định dạng (HTML Table)",
      desc: "Giữ nguyên màu ô, viền đen, ô gộp và số liệu. Phù hợp dán vào Teams, Word, Excel, và TAMMI có hỗ trợ bảng.",
      icon: <Table className="w-5 h-5 text-primary" />,
      recommended: true
    },
    {
      mode: "image",
      label: "Copy dạng ảnh (PNG sắc nét)",
      desc: "Chụp ảnh bảng và sao chép trực tiếp vào Clipboard. Đảm bảo 100% hiển thị đẹp khi dán vào mọi nhóm chat TAMMI.",
      icon: <ImageIcon className="w-5 h-5 text-blue-500" />
    },
    {
      mode: "tsv",
      label: "Copy cho Microsoft Excel (TSV)",
      desc: "Định dạng phân tách bằng Tab, sẵn sàng dán trực tiếp vào bảng tính Excel mà không bị lệch cột.",
      icon: <FileSpreadsheet className="w-5 h-5 text-emerald-500" />
    },
    {
      mode: "text",
      label: "Copy văn bản rút gọn (Plain Text)",
      desc: "Văn bản thuần không định dạng, tương thích tuyệt đối với mọi ứng dụng tin nhắn nhanh.",
      icon: <FileText className="w-5 h-5 text-amber-500" />
    }
  ];

  const handleCopy = async () => {
    setIsCopying(true);
    try {
      const ok = await onConfirmCopy(selectedMode);
      if (ok) {
        addToast({
          type: "success",
          title: "Đã sao chép vào Clipboard",
          message: `Dữ liệu đã được nạp vào Clipboard với chế độ: ${
            selectedMode === "html"
              ? "Bảng có định dạng (HTML)"
              : selectedMode === "image"
              ? "Hình ảnh PNG"
              : selectedMode === "tsv"
              ? "Dữ liệu Excel (TSV)"
              : "Văn bản thuần"
          }. Bạn có thể mở TAMMI và nhấn Ctrl+V.`
        });
        onClose();
      } else {
        throw new Error("Không thể ghi vào hệ thống Clipboard.");
      }
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi sao chép", message: err.message });
    } finally {
      setIsCopying(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} size="md">
      <div className="space-y-4 text-xs">
        <div className="p-3 bg-primary-subtle/50 border border-primary/20 rounded-xl flex items-start gap-2.5 text-foreground">
          <Info className="w-4 h-4 text-primary shrink-0 mt-0.5" />
          <div className="text-[11px] leading-relaxed">
            Nếu ứng dụng TAMMI trên máy bạn khi dán bằng HTML bị mất viền hoặc định dạng, hãy chọn{" "}
            <span className="font-bold text-primary">Copy dạng ảnh (PNG)</span> để giữ hình ảnh bảng hoàn hảo 100%.
          </div>
        </div>

        <div className="space-y-2">
          {options.map((opt) => {
            const isSelected = selectedMode === opt.mode;
            return (
              <div
                key={opt.mode}
                onClick={() => setSelectedMode(opt.mode)}
                className={`p-3.5 rounded-xl border transition-all cursor-pointer flex items-start gap-3 ${
                  isSelected
                    ? "bg-primary-subtle border-primary text-foreground shadow-xs"
                    : "bg-surface border-border hover:border-border-strong text-muted hover:text-foreground"
                }`}
              >
                <div className="p-2 rounded-lg bg-surface border border-border shrink-0">
                  {opt.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-xs text-foreground">{opt.label}</span>
                    {opt.recommended && (
                      <span className="text-[10px] bg-primary text-primary-foreground font-bold px-1.5 py-0.2 rounded">
                        Mặc định
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] text-muted mt-1 leading-relaxed">{opt.desc}</div>
                </div>
                <div className="mt-1">
                  <input
                    type="radio"
                    name="copy_mode"
                    checked={isSelected}
                    onChange={() => setSelectedMode(opt.mode)}
                    className="accent-primary w-4 h-4 cursor-pointer"
                  />
                </div>
              </div>
            );
          })}
        </div>

        <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-border">
          <Button variant="outline" size="sm" onClick={onClose} disabled={isCopying}>
            Hủy
          </Button>
          <Button size="sm" onClick={handleCopy} isLoading={isCopying} icon={<Copy className="w-4 h-4" />}>
            {isCopying ? "Đang sao chép..." : "Sao chép ngay"}
          </Button>
        </div>
      </div>
    </Modal>
  );
};
