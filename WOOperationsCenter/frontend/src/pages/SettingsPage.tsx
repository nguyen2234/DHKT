import React, { useState, useEffect } from "react";
import { bridge } from "../services/bridge";
import { useAppStore } from "../stores/appStore";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import {
  Settings,
  FolderOpen,
  Save,
  Sun,
  Moon,
  Database,
  Layers,
  Sparkles,
  ShieldCheck,
  RotateCcw
} from "lucide-react";

export const SettingsPage: React.FC = () => {
  const { theme, toggleTheme, addToast } = useAppStore();
  const [config, setConfig] = useState<any>(null);
  const [outputDir, setOutputDir] = useState<string>("");
  const [recipient, setRecipient] = useState<string>("");
  const [deadlineQh, setDeadlineQh] = useState<string>("");
  const [deadlineMonth, setDeadlineMonth] = useState<string>("");
  const [tagFormat, setTagFormat] = useState<string>("name");
  const [isSaving, setIsSaving] = useState<boolean>(false);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const cfg = await bridge.getAppConfig();
      setConfig(cfg);
      setOutputDir(cfg.default_output_dir || "C:\\Reports");
      if (cfg.executive_report) {
        setRecipient(cfg.executive_report.recipient || "");
        setDeadlineQh(cfg.executive_report.deadline_qh || "30/09");
        setDeadlineMonth(cfg.executive_report.deadline_month || "05/10");
      }
      if (cfg.thft_report) {
        setTagFormat(cfg.thft_report.tag_format || "name");
      }
    } catch (err: any) {
      console.error(err);
    }
  };

  const handlePickDirectory = async () => {
    try {
      const selected = await bridge.pickDirectory();
      if (selected) {
        setOutputDir(selected);
      }
    } catch (err: any) {
      console.error(err);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const updated = {
        ...config,
        default_output_dir: outputDir,
        executive_report: {
          ...config.executive_report,
          recipient,
          deadline_qh: deadlineQh,
          deadline_month: deadlineMonth
        },
        thft_report: {
          ...config.thft_report,
          tag_format: tagFormat
        }
      };

      const ok = await bridge.saveAppConfig(updated);
      if (ok) {
        setConfig(updated);
        addToast({
          type: "success",
          title: "Đã lưu cài đặt",
          message: "Cấu hình đã được lưu an toàn trong thư mục Windows AppData."
        });
      } else {
        throw new Error("Không thể ghi file cấu hình");
      }
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi lưu cấu hình", message: err.message });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Cài đặt Hệ thống (Module F)
          </h1>
          <p className="text-xs text-muted mt-1">
            Quản lý tùy chọn lưu trữ, thư mục xuất báo cáo, giao diện và cấu hình mapping Excel.
          </p>
        </div>

        <Button
          size="sm"
          onClick={handleSave}
          isLoading={isSaving}
          icon={<Save className="w-4 h-4" />}
        >
          Lưu tất cả thay đổi
        </Button>
      </div>

      {/* General Settings */}
      <Card
        header={
          <div className="flex items-center gap-2">
            <Settings className="w-4 h-4 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">Tùy chọn Chung & Giao diện</h3>
          </div>
        }
      >
        <div className="space-y-4 text-xs">
          {/* Theme switcher */}
          <div className="flex items-center justify-between py-2 border-b border-border">
            <div>
              <div className="font-semibold text-foreground">Giao diện (Theme)</div>
              <div className="text-muted text-[11px] mt-0.5">
                Chuyển đổi giữa chế độ Sáng (Light) và Tối (Dark)
              </div>
            </div>
            <button
              onClick={toggleTheme}
              className="px-3 py-1.5 rounded-lg border border-border-strong bg-background text-foreground hover:bg-item-hover font-medium flex items-center gap-2 cursor-pointer transition-colors"
            >
              {theme === "light" ? <Sun className="w-4 h-4 text-warning" /> : <Moon className="w-4 h-4 text-primary" />}
              <span>{theme === "light" ? "Chế độ Sáng" : "Chế độ Tối"}</span>
            </button>
          </div>

          {/* Default Output Folder */}
          <div className="py-2 border-b border-border">
            <div className="font-semibold text-foreground mb-1">Thư mục xuất báo cáo mặc định:</div>
            <div className="flex items-center gap-2 mt-1.5">
              <input
                type="text"
                value={outputDir}
                onChange={(e) => setOutputDir(e.target.value)}
                className="flex-1 bg-background border border-border-strong rounded-lg px-3 py-2 text-foreground focus:outline-none"
              />
              <Button
                variant="outline"
                size="sm"
                onClick={handlePickDirectory}
                icon={<FolderOpen className="w-4 h-4" />}
              >
                Chọn thư mục
              </Button>
            </div>
          </div>

          {/* Storage Information */}
          <div className="flex items-center justify-between py-2">
            <div>
              <div className="font-semibold text-foreground">Vị trí lưu cấu hình & SQLite:</div>
              <div className="text-muted font-mono text-[11px] mt-0.5">
                %APPDATA%\WOOperationsCenter
              </div>
            </div>
            <Badge variant="success" size="sm">
              An toàn & Tự động
            </Badge>
          </div>
        </div>
      </Card>

      {/* Default Template Values */}
      <Card
        header={
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">Giá trị Báo cáo Mặc định</h3>
          </div>
        }
      >
        <div className="space-y-4 text-xs">
          <div>
            <label className="font-semibold text-foreground block mb-1">Người nhận mặc định:</label>
            <input
              type="text"
              value={recipient}
              onChange={(e) => setRecipient(e.target.value)}
              className="w-full bg-background border border-border-strong rounded-lg px-3 py-2 text-foreground focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="font-semibold text-foreground block mb-1">Hạn chót WO quá hạn mặc định:</label>
              <input
                type="text"
                value={deadlineQh}
                onChange={(e) => setDeadlineQh(e.target.value)}
                className="w-full bg-background border border-border-strong rounded-lg px-3 py-2 text-foreground focus:outline-none"
              />
            </div>

            <div>
              <label className="font-semibold text-foreground block mb-1">Hạn chót WO tháng mặc định:</label>
              <input
                type="text"
                value={deadlineMonth}
                onChange={(e) => setDeadlineMonth(e.target.value)}
                className="w-full bg-background border border-border-strong rounded-lg px-3 py-2 text-foreground focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="font-semibold text-foreground block mb-1">Định dạng Token TAG mặc định:</label>
            <select
              value={tagFormat}
              onChange={(e) => setTagFormat(e.target.value)}
              className="w-full bg-background border border-border-strong rounded-lg px-3 py-2 text-foreground focus:outline-none"
            >
              <option value="name">@Họ và tên (@Đinh Xuân Hương)</option>
              <option value="name_upper">@HỌ VÀ TÊN (@ĐINH XUÂN HƯƠNG)</option>
              <option value="username">@username (@huongdx3)</option>
              <option value="ft_username">@FT username (@FT huongdx3)</option>
              <option value="user_pos_center">@username VịTrí Huyện (@huongdx3 NVDM DCU)</option>
            </select>
          </div>
        </div>
      </Card>
    </div>
  );
};
