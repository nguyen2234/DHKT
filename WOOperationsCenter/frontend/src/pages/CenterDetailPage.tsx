import React, { useState, useEffect, useRef, useMemo } from "react";
import { useAppStore } from "../stores/appStore";
import { bridge, EmployeeData, WorkOrderItem } from "../services/bridge";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { KpiCard } from "../components/ui/KpiCard";
import { ExportModal } from "../components/modals/ExportModal";
import { CopyModeModal } from "../components/modals/CopyModeModal";
import { copyFormattedTable, ClipboardCopyMode } from "../services/clipboardHelper";
import {
  Building2,
  Users,
  Copy,
  Download,
  AlertTriangle,
  Clock,
  ArrowLeft,
  Check,
  Tag,
  CheckSquare,
  Square,
  FileText,
  Search,
  ChevronLeft,
  ChevronRight,
  Filter,
  RotateCcw,
  ExternalLink,
  Table as TableIcon
} from "lucide-react";

export const CenterDetailPage: React.FC = () => {
  const { dataset, selectedCenterCode, setSelectedCenterCode, setCurrentRoute, addToast } = useAppStore();

  const [activeTab, setActiveTab] = useState<"ft" | "overdue" | "pending">("ft");
  const [positionFilter, setPositionFilter] = useState<"Tất cả" | "NV DM" | "NV NHÀ TRẠM">("Tất cả");
  const [centerSearch, setCenterSearch] = useState<string>("");

  const [centerData, setCenterData] = useState<any>(null);
  const [employees, setEmployees] = useState<EmployeeData[]>([]);
  const [notification, setNotification] = useState<string>("");
  const [isNotifEdited, setIsNotifEdited] = useState<boolean>(false);
  const [deadline, setDeadline] = useState<string>("05/10");
  const [meetingTime, setMeetingTime] = useState<string>("06:30");
  const [tagFormat, setTagFormat] = useState<"name" | "username">("name");

  const [overdueWos, setOverdueWos] = useState<WorkOrderItem[]>([]);
  const [pendingWos, setPendingWos] = useState<WorkOrderItem[]>([]);
  const [copiedAction, setCopiedAction] = useState<string | null>(null);

  // Modals
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [isCopyTableModalOpen, setIsCopyTableModalOpen] = useState(false);
  const [copyTarget, setCopyTarget] = useState<"all" | "ft" | "overdue" | "pending" | null>(null);

  const ftTableRef = useRef<HTMLDivElement>(null);
  const overdueTableRef = useRef<HTMLDivElement>(null);
  const pendingTableRef = useRef<HTMLDivElement>(null);

  const centersList = dataset?.centers || [];
  const currentCenterCode = selectedCenterCode || (centersList[0]?.code ?? "DCU");
  const currentCenterIndex = centersList.findIndex((c) => c.code === currentCenterCode);
  const centerMeta = centersList.find((c) => c.code === currentCenterCode);

  useEffect(() => {
    if (currentCenterCode && dataset) {
      loadCenterInfo();
    }
  }, [currentCenterCode, dataset]);

  const loadCenterInfo = async () => {
    try {
      const details = await bridge.getCenterDetails(currentCenterCode);
      setCenterData(details);
      setEmployees(details.employees || []);
      setNotification(details.notification || "");
      setIsNotifEdited(false);

      const overdueRes = await bridge.queryWorkOrders({
        center_code: currentCenterCode,
        classification: "overdue",
        page_size: 300
      });
      setOverdueWos(overdueRes.items);

      const pendingRes = await bridge.queryWorkOrders({
        center_code: currentCenterCode,
        classification: "pending",
        page_size: 300
      });
      setPendingWos(pendingRes.items);
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi tải thông tin huyện", message: err.message });
    }
  };

  // Switch between Next and Previous districts
  const handleNavigateCenter = (direction: "prev" | "next") => {
    if (centersList.length === 0) return;
    let nextIdx = direction === "next" ? currentCenterIndex + 1 : currentCenterIndex - 1;
    if (nextIdx < 0) nextIdx = centersList.length - 1;
    if (nextIdx >= centersList.length) nextIdx = 0;
    setSelectedCenterCode(centersList[nextIdx].code);
  };

  // Filter employees according to position filter
  const filteredEmployees = useMemo(() => {
    return employees.filter((emp) => {
      if (positionFilter === "NV DM") {
        return emp.position.toUpperCase().includes("DM");
      }
      if (positionFilter === "NV NHÀ TRẠM") {
        const p = emp.position.toUpperCase();
        return p.includes("TRẠM") || p.includes("TRAM");
      }
      return true;
    });
  }, [employees, positionFilter]);

  // Recalculate TAG list based on filtered employees
  const taggedEmployees = useMemo(() => {
    return filteredEmployees.filter((e) => e.is_tagged);
  }, [filteredEmployees]);

  // Regenerate notification text when deadline, meeting time, format or tags change
  const buildNotificationText = () => {
    if (!dataset || !centerMeta) return "";
    const tags = taggedEmployees
      .map((e) => (tagFormat === "username" ? `@${e.username}` : `@${e.full_name}`))
      .join(" ");

    return `FT tồn quá hạn wo đến ngày hôm nay ${dataset.day_month_str}, khẩn trương hoàn thành trước ${deadline}. FT không có tiến độ ngày sẽ triệu tập họp vào ${meetingTime} ngày mai\n\n${tags}`;
  };

  const handleRegenerateNotif = () => {
    const text = buildNotificationText();
    setNotification(text);
    setIsNotifEdited(false);
  };

  const handleToggleTag = async (emp: EmployeeData) => {
    const nextState = !emp.is_tagged;
    try {
      await bridge.setEmployeeTag(emp.center_code, emp.username, nextState);
      setEmployees((prev) =>
        prev.map((e) =>
          e.username === emp.username ? { ...e, is_tagged: nextState, is_manually_tagged: nextState } : e
        )
      );
      if (!isNotifEdited) {
        setTimeout(handleRegenerateNotif, 50);
      }
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi TAG", message: err.message });
    }
  };

  // Subtotal calculations for filtered employees
  const subtotal = useMemo(() => {
    return filteredEmployees.reduce(
      (acc, e) => {
        acc.ton += e.ton;
        acc.qua_han += e.qua_han;
        acc.qua_han_30 += e.qua_han_30;
        acc.thuc_hien_ngay += e.thuc_hien_ngay;
        acc.icms_bd_nt_ton += e.icms_bd_nt_ton;
        acc.icms_bd_nt_qh += e.icms_bd_nt_qh;
        acc.icms_bd_nt_qh30 += e.icms_bd_nt_qh30;
        acc.icms_bd_thc_ton += e.icms_bd_thc_ton;
        acc.icms_bd_thc_qh += e.icms_bd_thc_qh;
        acc.icms_bd_thc_qh30 += e.icms_bd_thc_qh30;
        acc.icms_tt_tc_ton += e.icms_tt_tc_ton;
        acc.icms_tt_tc_qh += e.icms_tt_tc_qh;
        acc.icms_tt_tc_qh30 += e.icms_tt_tc_qh30;
        acc.bao_hong_ton += e.bao_hong_ton;
        acc.bao_hong_qh += e.bao_hong_qh;
        acc.bao_hong_qh30 += e.bao_hong_qh30;
        return acc;
      },
      {
        ton: 0,
        qua_han: 0,
        qua_han_30: 0,
        thuc_hien_ngay: 0,
        icms_bd_nt_ton: 0,
        icms_bd_nt_qh: 0,
        icms_bd_nt_qh30: 0,
        icms_bd_thc_ton: 0,
        icms_bd_thc_qh: 0,
        icms_bd_thc_qh30: 0,
        icms_tt_tc_ton: 0,
        icms_tt_tc_qh: 0,
        icms_tt_tc_qh30: 0,
        bao_hong_ton: 0,
        bao_hong_qh: 0,
        bao_hong_qh30: 0
      }
    );
  }, [filteredEmployees]);

  // Build HTML table for FT employees
  const buildFtHtmlTable = () => {
    const num = (v: number) => (v > 0 ? String(v) : "");
    const rows = filteredEmployees.map((e) => `
      <tr style="background-color: ${e.is_tagged ? "#fff5f5" : "#ffffff"};">
        <td style="border: 1px solid #000; text-align: left;">${e.username}</td>
        <td style="border: 1px solid #000; text-align: left;">${e.full_name}</td>
        <td style="border: 1px solid #000; text-align: center;">${e.center_code}</td>
        <td style="border: 1px solid #000; text-align: center;">${e.position}</td>
        <td style="border: 1px solid #000; text-align: right;">${num(e.icms_bd_nt_ton)}</td>
        <td style="border: 1px solid #000; text-align: right;">${num(e.icms_bd_nt_qh)}</td>
        <td style="border: 1px solid #000; text-align: right;">${num(e.icms_bd_nt_qh30)}</td>
        <td style="border: 1px solid #000; text-align: right;">${num(e.icms_bd_thc_ton)}</td>
        <td style="border: 1px solid #000; text-align: right;">${num(e.icms_bd_thc_qh)}</td>
        <td style="border: 1px solid #000; text-align: right;">${num(e.icms_bd_thc_qh30)}</td>
        <td style="border: 1px solid #000; text-align: right;">${num(e.icms_tt_tc_ton)}</td>
        <td style="border: 1px solid #000; text-align: right;">${num(e.icms_tt_tc_qh)}</td>
        <td style="border: 1px solid #000; text-align: right;">${num(e.icms_tt_tc_qh30)}</td>
        <td style="border: 1px solid #000; text-align: right;">${num(e.bao_hong_ton)}</td>
        <td style="border: 1px solid #000; text-align: right;">${num(e.bao_hong_qh)}</td>
        <td style="border: 1px solid #000; text-align: right;">${num(e.bao_hong_qh30)}</td>
        <td style="border: 1px solid #000; text-align: right; font-weight: bold;">${num(e.ton)}</td>
        <td style="border: 1px solid #000; text-align: right; font-weight: bold; color: #dc2626;">${num(e.qua_han)}</td>
        <td style="border: 1px solid #000; text-align: right;">${num(e.qua_han_30)}</td>
        <td style="border: 1px solid #000; text-align: right; font-weight: bold; color: ${e.thuc_hien_ngay > 0 ? "#000" : "#dc2626"};">${num(e.thuc_hien_ngay)}</td>
      </tr>
    `).join("");

    return `
      <div style="font-family: Arial, sans-serif; font-size: 11px;">
        <table border="1" cellspacing="0" cellpadding="4" style="border-collapse: collapse; border: 1px solid #000; width: 100%; text-align: center;">
          <tr style="font-weight: bold;">
            <th rowspan="2" style="background-color: #92D050; border: 1px solid #000;">FT</th>
            <th rowspan="2" style="background-color: #92D050; border: 1px solid #000;">Tên FT</th>
            <th rowspan="2" style="background-color: #92D050; border: 1px solid #000;">TTH</th>
            <th rowspan="2" style="background-color: #92D050; border: 1px solid #000;">Vị trí</th>
            <th colspan="3" style="background-color: #EBF1DE; border: 1px solid #000;">ICMS_Bảo dưỡng nhà trạm</th>
            <th colspan="3" style="background-color: #FDE9D9; border: 1px solid #000;">ICMS_Bảo dưỡng THC</th>
            <th colspan="3" style="background-color: #92CDDC; border: 1px solid #000;">ICMS_Tuần tra tuyến cáp</th>
            <th colspan="3" style="background-color: #0070C0; color: #fff; border: 1px solid #000;">Báo hỏng hạ tầng mạng lưới</th>
            <th colspan="3" style="background-color: #92D050; border: 1px solid #000;">Tổng</th>
            <th rowspan="2" style="background-color: #FF0000; color: #fff; border: 1px solid #000;">Thực hiện ngày</th>
          </tr>
          <tr style="font-weight: bold;">
            <th style="border: 1px solid #000;">Tồn</th><th style="border: 1px solid #000;">Quá hạn</th><th style="border: 1px solid #000;">QH 30N</th>
            <th style="border: 1px solid #000;">Tồn</th><th style="border: 1px solid #000;">Quá hạn</th><th style="border: 1px solid #000;">QH 30N</th>
            <th style="border: 1px solid #000;">Tồn</th><th style="border: 1px solid #000;">Quá hạn</th><th style="border: 1px solid #000;">QH 30N</th>
            <th style="border: 1px solid #000;">Tồn</th><th style="border: 1px solid #000;">Quá hạn</th><th style="border: 1px solid #000;">QH 30N</th>
            <th style="border: 1px solid #000;">Tồn</th><th style="border: 1px solid #000;">Quá hạn</th><th style="border: 1px solid #000;">QH 30N</th>
          </tr>
          ${rows}
          <tr style="background-color: #FEF3C7; font-weight: bold;">
            <td colspan="4" style="border: 1px solid #000; text-align: left;">Tổng cộng (${filteredEmployees.length} FT - ${taggedEmployees.length} Tag):</td>
            <td style="border: 1px solid #000; text-align: right;">${num(subtotal.icms_bd_nt_ton)}</td>
            <td style="border: 1px solid #000; text-align: right;">${num(subtotal.icms_bd_nt_qh)}</td>
            <td style="border: 1px solid #000; text-align: right;">${num(subtotal.icms_bd_nt_qh30)}</td>
            <td style="border: 1px solid #000; text-align: right;">${num(subtotal.icms_bd_thc_ton)}</td>
            <td style="border: 1px solid #000; text-align: right;">${num(subtotal.icms_bd_thc_qh)}</td>
            <td style="border: 1px solid #000; text-align: right;">${num(subtotal.icms_bd_thc_qh30)}</td>
            <td style="border: 1px solid #000; text-align: right;">${num(subtotal.icms_tt_tc_ton)}</td>
            <td style="border: 1px solid #000; text-align: right;">${num(subtotal.icms_tt_tc_qh)}</td>
            <td style="border: 1px solid #000; text-align: right;">${num(subtotal.icms_tt_tc_qh30)}</td>
            <td style="border: 1px solid #000; text-align: right;">${num(subtotal.bao_hong_ton)}</td>
            <td style="border: 1px solid #000; text-align: right;">${num(subtotal.bao_hong_qh)}</td>
            <td style="border: 1px solid #000; text-align: right;">${num(subtotal.bao_hong_qh30)}</td>
            <td style="border: 1px solid #000; text-align: right;">${subtotal.ton}</td>
            <td style="border: 1px solid #000; text-align: right; color: #dc2626;">${subtotal.qua_han}</td>
            <td style="border: 1px solid #000; text-align: right;">${num(subtotal.qua_han_30)}</td>
            <td style="border: 1px solid #000; text-align: right; color: #dc2626;">${subtotal.thuc_hien_ngay}</td>
          </tr>
        </table>
      </div>
    `;
  };

  const buildFtTsv = () => {
    const headers1 = ["FT", "Tên FT", "TTH", "Vị trí", "BD NT Tồn", "BD NT QH", "BD NT QH30", "BD THC Tồn", "BD THC QH", "BD THC QH30", "TT TC Tồn", "TT TC QH", "TT TC QH30", "Báo Hỏng Tồn", "Báo Hỏng QH", "Báo Hỏng QH30", "Tổng Tồn", "Tổng QH", "Tổng QH30", "TH Ngày"];
    const lines = [headers1.join("\t")];
    filteredEmployees.forEach((e) => {
      lines.push([
        e.username, e.full_name, e.center_code, e.position,
        e.icms_bd_nt_ton, e.icms_bd_nt_qh, e.icms_bd_nt_qh30,
        e.icms_bd_thc_ton, e.icms_bd_thc_qh, e.icms_bd_thc_qh30,
        e.icms_tt_tc_ton, e.icms_tt_tc_qh, e.icms_tt_tc_qh30,
        e.bao_hong_ton, e.bao_hong_qh, e.bao_hong_qh30,
        e.ton, e.qua_han, e.qua_han_30, e.thuc_hien_ngay
      ].join("\t"));
    });
    lines.push([
      `Tổng cộng (${filteredEmployees.length} FT - ${taggedEmployees.length} Tag)`,
      "", currentCenterCode, positionFilter,
      subtotal.icms_bd_nt_ton, subtotal.icms_bd_nt_qh, subtotal.icms_bd_nt_qh30,
      subtotal.icms_bd_thc_ton, subtotal.icms_bd_thc_qh, subtotal.icms_bd_thc_qh30,
      subtotal.icms_tt_tc_ton, subtotal.icms_tt_tc_qh, subtotal.icms_tt_tc_qh30,
      subtotal.bao_hong_ton, subtotal.bao_hong_qh, subtotal.bao_hong_qh30,
      subtotal.ton, subtotal.qua_han, subtotal.qua_han_30, subtotal.thuc_hien_ngay
    ].join("\t"));
    return lines.join("\n");
  };

  const buildOverdueWoHtml = () => {
    const rows = overdueWos.map((w, idx) => `
      <tr style="background-color: ${idx % 2 === 0 ? "#ffffff" : "#f8fafc"};">
        <td style="border: 1px solid #000; text-align: center;">${idx + 1}</td>
        <td style="border: 1px solid #000; font-family: monospace;">${w.code}</td>
        <td style="border: 1px solid #000;">${w.job_type}</td>
        <td style="border: 1px solid #000;">${w.content}</td>
        <td style="border: 1px solid #000; text-align: center;">${w.deadline}</td>
        <td style="border: 1px solid #000; text-align: center;">${w.status}</td>
        <td style="border: 1px solid #000;">${w.performer}</td>
        <td style="border: 1px solid #000; text-align: center;">${w.station_code}</td>
        <td style="border: 1px solid #000; text-align: center; font-weight: bold; color: #1F4E78;">${w.overdue_days}</td>
      </tr>
    `).join("");

    return `
      <div style="font-family: Arial, sans-serif; font-size: 11px;">
        <h4 style="color: #1F4E78; margin-bottom: 6px;">DANH SÁCH CHI TIẾT WO QUÁ HẠN — ${centerMeta?.name || currentCenterCode} (${overdueWos.length} WO)</h4>
        <table border="1" cellspacing="0" cellpadding="4" style="border-collapse: collapse; border: 1px solid #000; width: 100%;">
          <tr style="background-color: #1F4E78; color: #ffffff; font-weight: bold; text-align: center;">
            <th style="border: 1px solid #000;">STT</th>
            <th style="border: 1px solid #000;">Mã công việc</th>
            <th style="border: 1px solid #000;">Loại công việc</th>
            <th style="border: 1px solid #000;">Nội dung công việc</th>
            <th style="border: 1px solid #000;">Thời điểm kết thúc</th>
            <th style="border: 1px solid #000;">Trạng thái</th>
            <th style="border: 1px solid #000;">Nhân viên</th>
            <th style="border: 1px solid #000;">Mã trạm</th>
            <th style="border: 1px solid #000;">Ngày quá hạn</th>
          </tr>
          ${rows}
        </table>
      </div>
    `;
  };

  const buildPendingWoHtml = () => {
    const rows = pendingWos.map((w, idx) => `
      <tr style="background-color: ${idx % 2 === 0 ? "#ffffff" : "#f8fafc"};">
        <td style="border: 1px solid #000; text-align: center;">${idx + 1}</td>
        <td style="border: 1px solid #000; font-family: monospace;">${w.code}</td>
        <td style="border: 1px solid #000;">${w.job_type}</td>
        <td style="border: 1px solid #000;">${w.content}</td>
        <td style="border: 1px solid #000; text-align: center;">${w.deadline}</td>
        <td style="border: 1px solid #000; text-align: center;">${w.status}</td>
        <td style="border: 1px solid #000;">${w.performer}</td>
        <td style="border: 1px solid #000; text-align: center;">${w.station_code}</td>
        <td style="border: 1px solid #000; text-align: center; font-weight: bold; color: #135E48;">+${w.overdue_days}</td>
      </tr>
    `).join("");

    return `
      <div style="font-family: Arial, sans-serif; font-size: 11px;">
        <h4 style="color: #135E48; margin-bottom: 6px;">DANH SÁCH CHI TIẾT WO TỒN CHƯA QUÁ HẠN — ${centerMeta?.name || currentCenterCode} (${pendingWos.length} WO)</h4>
        <table border="1" cellspacing="0" cellpadding="4" style="border-collapse: collapse; border: 1px solid #000; width: 100%;">
          <tr style="background-color: #135E48; color: #ffffff; font-weight: bold; text-align: center;">
            <th style="border: 1px solid #000;">STT</th>
            <th style="border: 1px solid #000;">Mã công việc</th>
            <th style="border: 1px solid #000;">Loại công việc</th>
            <th style="border: 1px solid #000;">Nội dung công việc</th>
            <th style="border: 1px solid #000;">Thời điểm kết thúc</th>
            <th style="border: 1px solid #000;">Trạng thái</th>
            <th style="border: 1px solid #000;">Nhân viên</th>
            <th style="border: 1px solid #000;">Mã trạm</th>
            <th style="border: 1px solid #000;">Số ngày còn lại</th>
          </tr>
          ${rows}
        </table>
      </div>
    `;
  };

  const handleConfirmCopyModal = async (mode: ClipboardCopyMode) => {
    if (copyTarget === "all") {
      const fullHtml = `
        <div style="font-family: Arial, sans-serif;">
          <div style="font-weight: bold; margin-bottom: 15px; line-height: 1.5; color: #1e293b;">
            ${notification.replace(/\n/g, "<br>")}
          </div>
          ${buildFtHtmlTable()}
          <br>
          ${buildOverdueWoHtml()}
          <br>
          ${buildPendingWoHtml()}
        </div>
      `;
      const fullTsv = `${notification}\n\n${buildFtTsv()}`;
      return await copyFormattedTable({
        element: ftTableRef.current,
        htmlContent: fullHtml,
        textContent: fullTsv,
        tsvContent: fullTsv,
        mode
      });
    }

    if (copyTarget === "ft") {
      return await copyFormattedTable({
        element: ftTableRef.current,
        htmlContent: buildFtHtmlTable(),
        textContent: buildFtTsv(),
        tsvContent: buildFtTsv(),
        mode
      });
    }

    if (copyTarget === "overdue") {
      return await copyFormattedTable({
        element: overdueTableRef.current,
        htmlContent: buildOverdueWoHtml(),
        textContent: overdueWos.map((w) => `${w.code}\t${w.performer}\t${w.deadline}`).join("\n"),
        tsvContent: overdueWos.map((w) => `${w.code}\t${w.performer}\t${w.deadline}`).join("\n"),
        mode
      });
    }

    if (copyTarget === "pending") {
      return await copyFormattedTable({
        element: pendingTableRef.current,
        htmlContent: buildPendingWoHtml(),
        textContent: pendingWos.map((w) => `${w.code}\t${w.performer}\t${w.deadline}`).join("\n"),
        tsvContent: pendingWos.map((w) => `${w.code}\t${w.performer}\t${w.deadline}`).join("\n"),
        mode
      });
    }

    return false;
  };

  const handleCopyNotifOnly = async () => {
    try {
      const ok = await bridge.copyToClipboard("text", { text: notification });
      if (ok) {
        setCopiedAction("notif");
        addToast({
          type: "success",
          title: "Đã copy Thông báo + TAG",
          message: "Nội dung thông báo và danh sách @TAG đã sẵn sàng để dán vào TAMMI."
        });
        setTimeout(() => setCopiedAction(null), 2500);
      }
    } catch (err: any) {
      addToast({ type: "error", title: "Lỗi sao chép", message: err.message });
    }
  };

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

  return (
    <div className="space-y-6">
      {/* ========================================================
          PHẦN A: BỘ LỌC & CHỌN ĐƠN VỊ HUYỆN
          ======================================================== */}
      <div className="bg-surface border border-border rounded-2xl p-5 shadow-xs space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          {/* District Selector & Navigation */}
          <div className="flex items-center flex-wrap gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentRoute("centers")}
              icon={<ArrowLeft className="w-4 h-4" />}
            >
              Lưới 14 huyện
            </Button>

            {/* Prev / Next Buttons */}
            <div className="flex items-center rounded-lg border border-border bg-background p-0.5">
              <button
                onClick={() => handleNavigateCenter("prev")}
                title="Huyện trước"
                className="p-1.5 hover:bg-surface rounded text-muted hover:text-foreground cursor-pointer"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <div className="px-3 py-1 font-bold text-sm text-foreground flex items-center gap-1.5 min-w-[140px] justify-center">
                <span className="bg-primary/10 text-primary px-1.5 py-0.5 rounded text-xs">
                  {currentCenterCode}
                </span>
                <span>{centerMeta?.name || currentCenterCode}</span>
              </div>
              <button
                onClick={() => handleNavigateCenter("next")}
                title="Huyện sau"
                className="p-1.5 hover:bg-surface rounded text-muted hover:text-foreground cursor-pointer"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            {/* District Dropdown Selector */}
            <select
              value={currentCenterCode}
              onChange={(e) => setSelectedCenterCode(e.target.value)}
              className="bg-background border border-border-strong rounded-lg px-3 py-2 text-xs font-semibold text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 cursor-pointer"
            >
              {centersList.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.code} — {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Position Filter Tabs */}
          <div className="flex items-center gap-1 bg-background p-1 rounded-xl border border-border text-xs">
            <span className="text-muted px-2 font-medium flex items-center gap-1">
              <Filter className="w-3.5 h-3.5" /> Vị trí:
            </span>
            {(["Tất cả", "NV DM", "NV NHÀ TRẠM"] as const).map((filter) => (
              <button
                key={filter}
                onClick={() => setPositionFilter(filter)}
                className={`px-3 py-1.5 rounded-lg font-semibold transition-all cursor-pointer ${
                  positionFilter === filter
                    ? "bg-primary text-primary-foreground shadow-xs"
                    : "text-muted hover:text-foreground hover:bg-surface"
                }`}
              >
                {filter}
              </button>
            ))}
          </div>
        </div>

        {/* ========================================================
            PHẦN E: ACTION TOOLBAR (Ưu tiên cao nhất)
            ======================================================== */}
        <div className="flex items-center justify-between flex-wrap gap-2.5 pt-3 border-t border-border">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted">Thao tác nhanh cho TAMMI:</span>
          </div>
          <div className="flex items-center flex-wrap gap-2">
            <Button
              size="sm"
              onClick={() => {
                setCopyTarget("all");
                setIsCopyTableModalOpen(true);
              }}
              icon={<Copy className="w-4 h-4" />}
            >
              Copy toàn bộ báo cáo huyện
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={handleCopyNotifOnly}
              icon={copiedAction === "notif" ? <Check className="w-4 h-4 text-success" /> : <Tag className="w-4 h-4 text-primary" />}
            >
              Copy thông báo + TAG
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setCopyTarget("ft");
                setIsCopyTableModalOpen(true);
              }}
              icon={<TableIcon className="w-4 h-4 text-primary" />}
            >
              Copy bảng FT
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setCopyTarget("overdue");
                setIsCopyTableModalOpen(true);
              }}
              icon={<AlertTriangle className="w-4 h-4 text-danger" />}
            >
              Copy WO quá hạn
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setCopyTarget("pending");
                setIsCopyTableModalOpen(true);
              }}
              icon={<Clock className="w-4 h-4 text-success" />}
            >
              Copy WO trong hạn
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsExportModalOpen(true)}
              icon={<Download className="w-4 h-4 text-primary" />}
            >
              Xuất Excel huyện
            </Button>
          </div>
        </div>
      </div>

      {/* ========================================================
          PHẦN B: THỐNG KÊ NHANH (KPI Cards)
          ======================================================== */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3.5">
        <KpiCard
          title="Tổng nhân sự FT"
          value={`${filteredEmployees.length} FT`}
          subtitle={`Lọc theo: ${positionFilter}`}
          variant="default"
          icon={<Users className="w-4 h-4" />}
        />
        <KpiCard
          title="FT cần TAG hôm nay"
          value={`${taggedEmployees.length} FT`}
          subtitle="Tồn > 0 và TH ngày = 0"
          variant="danger"
          icon={<Tag className="w-4 h-4" />}
        />
        <KpiCard
          title="Tổng WO tồn"
          value={`${subtotal.ton} WO`}
          subtitle={`Trung tâm ${centerMeta?.name}`}
          variant="default"
          icon={<FileText className="w-4 h-4" />}
        />
        <KpiCard
          title="WO quá hạn"
          value={`${subtotal.qua_han} WO`}
          subtitle={`${Math.round((subtotal.qua_han / (subtotal.ton || 1)) * 100)}% trên tổng tồn`}
          variant="danger"
          icon={<AlertTriangle className="w-4 h-4" />}
        />
        <KpiCard
          title="WO chưa quá hạn"
          value={`${pendingWos.length} WO`}
          subtitle="Còn hạn xử lý"
          variant="success"
          icon={<Clock className="w-4 h-4" />}
        />
      </div>

      {/* ========================================================
          PHẦN C: THÔNG BÁO & TAGGING
          ======================================================== */}
      <Card
        header={
          <div className="flex items-center justify-between w-full flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <Tag className="w-4 h-4 text-primary" />
              <h3 className="text-sm font-semibold text-foreground">
                Khung Soạn Thông báo & Cấu hình TAG — {centerMeta?.name}
              </h3>
              {isNotifEdited && <Badge variant="warning" size="sm">Đã sửa thủ công</Badge>}
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRegenerateNotif}
                icon={<RotateCcw className="w-3.5 h-3.5" />}
              >
                Sinh lại thông báo
              </Button>
              <Button
                size="sm"
                onClick={handleCopyNotifOnly}
                icon={copiedAction === "notif" ? <Check className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
              >
                {copiedAction === "notif" ? "Đã copy" : "Copy thông báo + TAG"}
              </Button>
            </div>
          </div>
        }
      >
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 text-xs">
          {/* Left: Input parameters */}
          <div className="lg:col-span-5 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="font-medium text-foreground block mb-1">Hạn hoàn thành:</label>
                <input
                  type="text"
                  value={deadline}
                  onChange={(e) => {
                    setDeadline(e.target.value);
                    if (!isNotifEdited) setTimeout(handleRegenerateNotif, 50);
                  }}
                  className="w-full bg-background border border-border-strong rounded-lg px-3 py-1.5 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </div>
              <div>
                <label className="font-medium text-foreground block mb-1">Giờ họp triệu tập:</label>
                <input
                  type="text"
                  value={meetingTime}
                  onChange={(e) => {
                    setMeetingTime(e.target.value);
                    if (!isNotifEdited) setTimeout(handleRegenerateNotif, 50);
                  }}
                  className="w-full bg-background border border-border-strong rounded-lg px-3 py-1.5 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-1">
              <span className="font-medium text-foreground">Định dạng TAG:</span>
              <div className="flex items-center gap-2">
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="radio"
                    name="tag_format"
                    checked={tagFormat === "name"}
                    onChange={() => {
                      setTagFormat("name");
                      if (!isNotifEdited) setTimeout(handleRegenerateNotif, 50);
                    }}
                    className="accent-primary"
                  />
                  <span>Họ và tên</span>
                </label>
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="radio"
                    name="tag_format"
                    checked={tagFormat === "username"}
                    onChange={() => {
                      setTagFormat("username");
                      if (!isNotifEdited) setTimeout(handleRegenerateNotif, 50);
                    }}
                    className="accent-primary"
                  />
                  <span>Tài khoản FT</span>
                </label>
              </div>
            </div>

            {/* Tagged employees chips */}
            <div className="pt-2">
              <label className="font-medium text-foreground block mb-1.5">
                Danh sách nhân viên bị TAG ({taggedEmployees.length} FT):
              </label>
              <div className="max-h-28 overflow-y-auto p-2 bg-background rounded-lg border border-border flex flex-wrap gap-1.5">
                {taggedEmployees.length === 0 ? (
                  <span className="text-muted text-[11px] italic">Không có nhân viên nào bị TAG</span>
                ) : (
                  taggedEmployees.map((e) => (
                    <span
                      key={e.username}
                      className="bg-danger-bg text-danger px-2 py-0.5 rounded text-[11px] font-medium flex items-center gap-1"
                    >
                      @{e.full_name}
                      <button
                        onClick={() => handleToggleTag(e)}
                        className="text-danger hover:opacity-75 cursor-pointer ml-0.5"
                        title="Bỏ tag"
                      >
                        ×
                      </button>
                    </span>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Right: Editable Notification Text */}
          <div className="lg:col-span-7">
            <label className="font-medium text-foreground block mb-1">Nội dung tin nhắn gửi TAMMI (có thể sửa):</label>
            <textarea
              rows={8}
              value={notification}
              onChange={(e) => {
                setNotification(e.target.value);
                setIsNotifEdited(true);
              }}
              className="w-full bg-background border border-border-strong rounded-xl p-3 font-mono text-xs text-foreground leading-relaxed focus:outline-none focus:ring-2 focus:ring-primary/20 resize-none select-text"
            />
          </div>
        </div>
      </Card>

      {/* ========================================================
          PHẦN D: BẢNG DỮ LIỆU (TABS)
          ======================================================== */}
      <div className="space-y-3">
        <div className="border-b border-border flex items-center gap-6 text-sm font-medium">
          <button
            onClick={() => setActiveTab("ft")}
            className={`pb-3 transition-colors cursor-pointer flex items-center gap-2 ${
              activeTab === "ft"
                ? "border-b-2 border-primary text-foreground font-semibold"
                : "text-muted hover:text-foreground"
            }`}
          >
            <Users className="w-4 h-4" />
            <span>Báo cáo Nhân viên FT ({filteredEmployees.length})</span>
            {taggedEmployees.length > 0 && <Badge variant="danger" size="sm">{taggedEmployees.length}</Badge>}
          </button>

          <button
            onClick={() => setActiveTab("overdue")}
            className={`pb-3 transition-colors cursor-pointer flex items-center gap-2 ${
              activeTab === "overdue"
                ? "border-b-2 border-primary text-foreground font-semibold"
                : "text-muted hover:text-foreground"
            }`}
          >
            <AlertTriangle className="w-4 h-4 text-danger" />
            <span>Bảng WO Quá hạn ({overdueWos.length})</span>
          </button>

          <button
            onClick={() => setActiveTab("pending")}
            className={`pb-3 transition-colors cursor-pointer flex items-center gap-2 ${
              activeTab === "pending"
                ? "border-b-2 border-primary text-foreground font-semibold"
                : "text-muted hover:text-foreground"
            }`}
          >
            <Clock className="w-4 h-4 text-success" />
            <span>Bảng WO Chưa quá hạn ({pendingWos.length})</span>
          </button>
        </div>

        {/* TAB 1: FT Employees Table */}
        {activeTab === "ft" && (
          <Card noPadding>
            <div ref={ftTableRef} className="overflow-x-auto max-h-[550px]">
              <table className="w-full text-xs text-left border-collapse select-text">
                <thead className="sticky top-0 z-10 font-bold text-[11px] text-center shadow-xs">
                  {/* Super Header Row 1 */}
                  <tr>
                    <th rowSpan={2} className="py-2.5 px-3 bg-[#92D050] border border-black text-black">TAG</th>
                    <th rowSpan={2} className="py-2.5 px-3 bg-[#92D050] border border-black text-black">Tài khoản (FT)</th>
                    <th rowSpan={2} className="py-2.5 px-3 bg-[#92D050] border border-black text-black">Họ và tên</th>
                    <th rowSpan={2} className="py-2.5 px-3 bg-[#92D050] border border-black text-black">TTH</th>
                    <th rowSpan={2} className="py-2.5 px-3 bg-[#92D050] border border-black text-black">Vị trí</th>
                    <th colSpan={3} className="py-1 px-2 bg-[#EBF1DE] border border-black text-black">ICMS_Bảo dưỡng nhà trạm</th>
                    <th colSpan={3} className="py-1 px-2 bg-[#FDE9D9] border border-black text-black">ICMS_Bảo dưỡng THC</th>
                    <th colSpan={3} className="py-1 px-2 bg-[#92CDDC] border border-black text-black">ICMS_Tuần tra tuyến cáp</th>
                    <th colSpan={3} className="py-1 px-2 bg-[#0070C0] border border-black text-white">Báo hỏng HTML</th>
                    <th colSpan={3} className="py-1 px-2 bg-[#92D050] border border-black text-black">Tổng cộng</th>
                    <th rowSpan={2} className="py-2.5 px-3 bg-[#FF0000] border border-black text-white">TH Ngày</th>
                  </tr>
                  {/* Header Row 2 */}
                  <tr className="bg-surface text-black">
                    <th className="py-1 px-2 border border-black">Tồn</th><th className="py-1 px-2 border border-black">QH</th><th className="py-1 px-2 border border-black">QH30</th>
                    <th className="py-1 px-2 border border-black">Tồn</th><th className="py-1 px-2 border border-black">QH</th><th className="py-1 px-2 border border-black">QH30</th>
                    <th className="py-1 px-2 border border-black">Tồn</th><th className="py-1 px-2 border border-black">QH</th><th className="py-1 px-2 border border-black">QH30</th>
                    <th className="py-1 px-2 border border-black">Tồn</th><th className="py-1 px-2 border border-black">QH</th><th className="py-1 px-2 border border-black">QH30</th>
                    <th className="py-1 px-2 border border-black">Tồn</th><th className="py-1 px-2 border border-black">QH</th><th className="py-1 px-2 border border-black">QH30</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredEmployees.map((emp) => (
                    <tr
                      key={emp.username}
                      className={`hover:bg-item-hover transition-colors ${
                        emp.is_tagged ? "bg-danger-bg/25" : ""
                      }`}
                    >
                      <td className="py-1.5 px-2 text-center border-r border-border">
                        <button
                          onClick={() => handleToggleTag(emp)}
                          title="Bật/Tắt TAG thủ công"
                          className="cursor-pointer text-muted hover:text-foreground"
                        >
                          {emp.is_tagged ? (
                            <CheckSquare className="w-4 h-4 text-danger inline" />
                          ) : (
                            <Square className="w-4 h-4 text-muted inline" />
                          )}
                        </button>
                      </td>
                      <td className="py-1.5 px-2.5 font-mono font-medium text-foreground">{emp.username}</td>
                      <td className="py-1.5 px-2.5 font-medium text-foreground whitespace-nowrap">{emp.full_name}</td>
                      <td className="py-1.5 px-2 text-center text-muted">{emp.center_code}</td>
                      <td className="py-1.5 px-2 text-center text-muted whitespace-nowrap">{emp.position}</td>

                      <td className="py-1.5 px-2 text-right">{emp.icms_bd_nt_ton || ""}</td>
                      <td className="py-1.5 px-2 text-right text-danger">{emp.icms_bd_nt_qh || ""}</td>
                      <td className="py-1.5 px-2 text-right text-warning">{emp.icms_bd_nt_qh30 || ""}</td>

                      <td className="py-1.5 px-2 text-right">{emp.icms_bd_thc_ton || ""}</td>
                      <td className="py-1.5 px-2 text-right text-danger">{emp.icms_bd_thc_qh || ""}</td>
                      <td className="py-1.5 px-2 text-right text-warning">{emp.icms_bd_thc_qh30 || ""}</td>

                      <td className="py-1.5 px-2 text-right">{emp.icms_tt_tc_ton || ""}</td>
                      <td className="py-1.5 px-2 text-right text-danger">{emp.icms_tt_tc_qh || ""}</td>
                      <td className="py-1.5 px-2 text-right text-warning">{emp.icms_tt_tc_qh30 || ""}</td>

                      <td className="py-1.5 px-2 text-right">{emp.bao_hong_ton || ""}</td>
                      <td className="py-1.5 px-2 text-right text-danger">{emp.bao_hong_qh || ""}</td>
                      <td className="py-1.5 px-2 text-right text-warning">{emp.bao_hong_qh30 || ""}</td>

                      <td className="py-1.5 px-2.5 text-right font-bold text-foreground">{emp.ton || ""}</td>
                      <td className="py-1.5 px-2.5 text-right font-bold text-danger">{emp.qua_han || ""}</td>
                      <td className="py-1.5 px-2.5 text-right font-semibold text-warning">{emp.qua_han_30 || ""}</td>

                      <td className={`py-1.5 px-2.5 text-right font-bold ${
                        emp.thuc_hien_ngay > 0 ? "text-success" : "text-danger"
                      }`}>
                        {emp.thuc_hien_ngay > 0 ? emp.thuc_hien_ngay : 0}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="bg-[#FEF3C7] font-bold text-black border-t-2 border-black sticky bottom-0">
                    <td colSpan={5} className="py-2 px-3 text-left">
                      Tổng cộng ({filteredEmployees.length} FT - {taggedEmployees.length} Tag):
                    </td>
                    <td className="py-2 px-2 text-right">{subtotal.icms_bd_nt_ton || ""}</td>
                    <td className="py-2 px-2 text-right">{subtotal.icms_bd_nt_qh || ""}</td>
                    <td className="py-2 px-2 text-right">{subtotal.icms_bd_nt_qh30 || ""}</td>
                    <td className="py-2 px-2 text-right">{subtotal.icms_bd_thc_ton || ""}</td>
                    <td className="py-2 px-2 text-right">{subtotal.icms_bd_thc_qh || ""}</td>
                    <td className="py-2 px-2 text-right">{subtotal.icms_bd_thc_qh30 || ""}</td>
                    <td className="py-2 px-2 text-right">{subtotal.icms_tt_tc_ton || ""}</td>
                    <td className="py-2 px-2 text-right">{subtotal.icms_tt_tc_qh || ""}</td>
                    <td className="py-2 px-2 text-right">{subtotal.icms_tt_tc_qh30 || ""}</td>
                    <td className="py-2 px-2 text-right">{subtotal.bao_hong_ton || ""}</td>
                    <td className="py-2 px-2 text-right">{subtotal.bao_hong_qh || ""}</td>
                    <td className="py-2 px-2 text-right">{subtotal.bao_hong_qh30 || ""}</td>
                    <td className="py-2 px-2.5 text-right">{subtotal.ton}</td>
                    <td className="py-2 px-2.5 text-right text-danger">{subtotal.qua_han}</td>
                    <td className="py-2 px-2.5 text-right">{subtotal.qua_han_30 || ""}</td>
                    <td className="py-2 px-2.5 text-right text-danger">{subtotal.thuc_hien_ngay}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </Card>
        )}

        {/* TAB 2: Overdue WO Table */}
        {activeTab === "overdue" && (
          <Card noPadding>
            <div ref={overdueTableRef} className="overflow-x-auto max-h-[550px]">
              <table className="w-full text-xs text-left border-collapse select-text">
                <thead className="bg-[#1F4E78] text-white font-semibold sticky top-0 uppercase text-[11px] shadow-xs">
                  <tr>
                    <th className="py-2.5 px-3 text-center">STT</th>
                    <th className="py-2.5 px-3">Mã WO</th>
                    <th className="py-2.5 px-3">Loại công việc</th>
                    <th className="py-2.5 px-3">Nội dung</th>
                    <th className="py-2.5 px-3 text-center">Hạn kết thúc</th>
                    <th className="py-2.5 px-3 text-center">Trạng thái</th>
                    <th className="py-2.5 px-3">Nhân viên</th>
                    <th className="py-2.5 px-3 text-center">Mã trạm</th>
                    <th className="py-2.5 px-3 text-center">Số ngày quá hạn</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {overdueWos.length === 0 ? (
                    <tr>
                      <td colSpan={9} className="py-8 text-center text-muted">
                        Không có công việc WO nào bị quá hạn tại {centerMeta?.name}.
                      </td>
                    </tr>
                  ) : (
                    overdueWos.map((w, idx) => (
                      <tr key={w.code + idx} className="hover:bg-item-hover transition-colors">
                        <td className="py-2 px-3 text-center text-muted">{idx + 1}</td>
                        <td className="py-2 px-3 font-mono font-medium text-foreground">{w.code}</td>
                        <td className="py-2 px-3 text-muted">{w.job_type}</td>
                        <td className="py-2 px-3 max-w-xs truncate text-foreground" title={w.content}>
                          {w.content}
                        </td>
                        <td className="py-2 px-3 text-center text-muted">{w.deadline}</td>
                        <td className="py-2 px-3 text-center">{w.status}</td>
                        <td className="py-2 px-3 font-medium text-foreground">{w.performer}</td>
                        <td className="py-2 px-3 text-center font-mono text-muted">{w.station_code}</td>
                        <td className="py-2 px-3 text-center font-bold text-danger">{w.overdue_days} ngày</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {/* TAB 3: Pending WO Table */}
        {activeTab === "pending" && (
          <Card noPadding>
            <div ref={pendingTableRef} className="overflow-x-auto max-h-[550px]">
              <table className="w-full text-xs text-left border-collapse select-text">
                <thead className="bg-[#135E48] text-white font-semibold sticky top-0 uppercase text-[11px] shadow-xs">
                  <tr>
                    <th className="py-2.5 px-3 text-center">STT</th>
                    <th className="py-2.5 px-3">Mã WO</th>
                    <th className="py-2.5 px-3">Loại công việc</th>
                    <th className="py-2.5 px-3">Nội dung</th>
                    <th className="py-2.5 px-3 text-center">Hạn kết thúc</th>
                    <th className="py-2.5 px-3 text-center">Trạng thái</th>
                    <th className="py-2.5 px-3">Nhân viên</th>
                    <th className="py-2.5 px-3 text-center">Mã trạm</th>
                    <th className="py-2.5 px-3 text-center">Số ngày còn lại</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {pendingWos.length === 0 ? (
                    <tr>
                      <td colSpan={9} className="py-8 text-center text-muted">
                        Không có công việc WO tồn trong hạn.
                      </td>
                    </tr>
                  ) : (
                    pendingWos.map((w, idx) => (
                      <tr key={w.code + idx} className="hover:bg-item-hover transition-colors">
                        <td className="py-2 px-3 text-center text-muted">{idx + 1}</td>
                        <td className="py-2 px-3 font-mono font-medium text-foreground">{w.code}</td>
                        <td className="py-2 px-3 text-muted">{w.job_type}</td>
                        <td className="py-2 px-3 max-w-xs truncate text-foreground" title={w.content}>
                          {w.content}
                        </td>
                        <td className="py-2 px-3 text-center text-muted">{w.deadline}</td>
                        <td className="py-2 px-3 text-center">{w.status}</td>
                        <td className="py-2 px-3 font-medium text-foreground">{w.performer}</td>
                        <td className="py-2 px-3 text-center font-mono text-muted">{w.station_code}</td>
                        <td className="py-2 px-3 text-center font-bold text-success">+{w.overdue_days} ngày</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>

      {/* Export Modal Dialog */}
      <ExportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        reportType="thft_excel"
        centerCode={currentCenterCode}
        positionFilter={positionFilter}
      />

      {/* Copy Mode Modal Dialog */}
      <CopyModeModal
        isOpen={isCopyTableModalOpen}
        onClose={() => {
          setIsCopyTableModalOpen(false);
          setCopyTarget(null);
        }}
        title={`Sao chép ${
          copyTarget === "all"
            ? `Toàn bộ Báo cáo huyện ${centerMeta?.name || currentCenterCode}`
            : copyTarget === "ft"
            ? `Bảng Nhân sự FT — ${centerMeta?.name}`
            : copyTarget === "overdue"
            ? `Bảng WO Quá hạn — ${centerMeta?.name}`
            : `Bảng WO Chưa quá hạn — ${centerMeta?.name}`
        } cho TAMMI`}
        onConfirmCopy={handleConfirmCopyModal}
      />
    </div>
  );
};
