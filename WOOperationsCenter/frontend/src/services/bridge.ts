/**
 * Python-React Bridge Client for WO Operations Center.
 * Handles QWebChannel communication with Qt host, with automatic
 * browser-mode fallback for development and responsive UI testing.
 */

export interface ProvinceSummary {
  day: number;
  month: number;
  year: number;
  thuc_hien_ngay: number;
  tong_ton: number;
  ton_qua_han: number;
  ton_tren_30_ngay: number;
  top_centers: string[];
  overdue_30_centers: [string, number][];
  has_discrepancy: boolean;
  discrepancy_details: string;
}

export interface CenterOverview {
  code: string;
  name: string;
  full_name: string;
  total_employees: number;
  tagged_employees: number;
  overdue_wos: number;
  pending_wos: number;
  boundary_wos: number;
  tong_ton: number;
  ton_qua_han: number;
  ton_30_ngay: number;
  thuc_hien_ngay: number;
  kh_ngay: number;
  ty_le_ht_ngay: number;
  danh_gia: string;
  hop_ngay: string;
}

export interface DatasetSummary {
  file_path: string;
  file_fingerprint: string;
  detected_sheets: string[];
  report_date_str: string;
  day_month_str: string;
  deadline_str: string;
  meeting_time_str: string;
  total_employees: number;
  total_tagged: number;
  total_work_orders: number;
  total_pending_work_orders: number;
  total_boundary_work_orders: number;
  province_summary: ProvinceSummary;
  centers: CenterOverview[];
}

export interface EmployeeData {
  row_idx: number;
  username: string;
  full_name: string;
  position: string;
  center_code: string;
  ton: number;
  qua_han: number;
  qua_han_30: number;
  thuc_hien_ngay: number;
  should_tag: boolean;
  is_manually_tagged: boolean | null;
  is_tagged: boolean;
  icms_bd_nt_ton: number;
  icms_bd_nt_qh: number;
  icms_bd_nt_qh30: number;
  icms_bd_thc_ton: number;
  icms_bd_thc_qh: number;
  icms_bd_thc_qh30: number;
  icms_tt_tc_ton: number;
  icms_tt_tc_qh: number;
  icms_tt_tc_qh30: number;
  bao_hong_ton: number;
  bao_hong_qh: number;
  bao_hong_qh30: number;
}

export interface WorkOrderItem {
  stt: number | string;
  code: string;
  job_type: string;
  content: string;
  deadline: string;
  status: string;
  performer: string;
  station_code: string;
  ft_comment: string;
  ft_mobile: string;
  completed_date: string;
  overdue_days: number | string;
  center_code: string;
  center_name: string;
  bkk: string;
  bkk_reason: string;
  classification: "overdue" | "pending" | "boundary";
}

export interface ReportHistoryItem {
  id: number;
  timestamp: string;
  report_type: string;
  report_date: string;
  source_file_path: string;
  source_file_fingerprint: string;
  applied_filters: string;
  center_selection: string;
  output_path: string;
  message_snapshot: string;
  status: string;
}

// Global declaration for Qt WebChannel transport
declare global {
  interface Window {
    qt?: {
      webChannelTransport: any;
    };
    QWebChannel?: any;
    pyBridge?: any;
  }
}

class BridgeService {
  private pyBridge: any = null;
  private isConnected = false;
  private connectionPromise: Promise<void> | null = null;
  private progressListeners: ((pct: number, msg: string) => void)[] = [];

  constructor() {
    this.init();
  }

  private init(): Promise<void> {
    if (this.connectionPromise) return this.connectionPromise;

    this.connectionPromise = new Promise((resolve) => {
      const qtObj = typeof window !== "undefined" ? window.qt : undefined;
      if (qtObj && qtObj.webChannelTransport) {
        this.loadQWebChannelScript(() => {
          if (window.QWebChannel) {
            new window.QWebChannel(qtObj.webChannelTransport, (channel: any) => {
              this.pyBridge = channel.objects.pyBridge;
              this.isConnected = true;
              console.log("[Bridge] Connected to Python desktop backend.");

              // Connect signals
              if (this.pyBridge.importProgress) {
                this.pyBridge.importProgress.connect((pct: number, msg: string) => {
                  this.progressListeners.forEach((l) => l(pct, msg));
                });
              }

              resolve();
            });
          } else {
            resolve();
          }
        });
      } else {
        // Fallback browser mode
        console.warn("[Bridge] Running in standalone web mode (Mock / API fallback enabled).");
        resolve();
      }
    });

    return this.connectionPromise;
  }

  private loadQWebChannelScript(cb: () => void) {
    if (window.QWebChannel) return cb();
    const script = document.createElement("script");
    script.src = "qrc:///qtwebchannel/qwebchannel.js";
    script.onload = () => cb();
    script.onerror = () => {
      // Inline lightweight QWebChannel client implementation if qrc fails
      this.injectFallbackQWebChannel();
      cb();
    };
    document.head.appendChild(script);
  }

  private injectFallbackQWebChannel() {
    // If running in dev server, mock qwebchannel client
  }

  public onProgress(listener: (pct: number, msg: string) => void) {
    this.progressListeners.push(listener);
    return () => {
      this.progressListeners = this.progressListeners.filter((l) => l !== listener);
    };
  }

  // ==========================================
  // APIS
  // ==========================================

  public async pickExcelFile(): Promise<string> {
    await this.init();
    if (this.pyBridge && this.pyBridge.pickExcelFile) {
      return await new Promise((res) => this.pyBridge.pickExcelFile(res));
    }
    return "samples/ĐH WO UT1 (05102026) (1).xlsx";
  }

  public async pickDirectory(): Promise<string> {
    await this.init();
    if (this.pyBridge && this.pyBridge.pickDirectory) {
      return await new Promise((res) => this.pyBridge.pickDirectory(res));
    }
    return "C:\\Reports";
  }

  public async loadExcelDataset(filePath: string): Promise<DatasetSummary> {
    await this.init();
    if (this.pyBridge && this.pyBridge.loadExcelDataset) {
      const resStr: string = await new Promise((res) => this.pyBridge.loadExcelDataset(filePath, res));
      const res = JSON.parse(resStr);
      if (!res.success) throw new Error(res.error || "Không thể nạp tệp Excel");
      return res.data;
    }
    // Browser Mock Data matching actual workbook
    return this.getMockDataset();
  }

  public async getLoadedDataset(): Promise<DatasetSummary | null> {
    await this.init();
    if (this.pyBridge && this.pyBridge.getLoadedDataset) {
      const resStr: string = await new Promise((res) => this.pyBridge.getLoadedDataset(res));
      const res = JSON.parse(resStr);
      if (res.loaded && res.data) return res.data;
      return null;
    }
    return this.getMockDataset();
  }

  public async getAppConfig(): Promise<any> {
    await this.init();
    if (this.pyBridge && this.pyBridge.getAppConfig) {
      const str: string = await new Promise((res) => this.pyBridge.getAppConfig(res));
      return JSON.parse(str);
    }
    return {
      version: "1.0.0",
      theme: "light",
      recent_files: ["samples/ĐH WO UT1 (05102026) (1).xlsx"],
      default_output_dir: "C:\\Reports",
      executive_report: {
        recipient: "Kính gửi PGĐ @NAN PGĐ A THẮNG , TP @A Sơnpb1 TPKT NAN , TTH!",
        notification: "Đóng Wo quá hạn trước 30/9.\nĐóng hết wo tháng 9 xong trước 05/10.",
        deadline_qh: "30/09",
        deadline_month: "05/10"
      },
      thft_report: {
        deadline: "05/10",
        meeting_time: "06:30",
        tag_format: "name",
        position_filter: "Tất cả"
      }
    };
  }

  public async saveAppConfig(config: any): Promise<boolean> {
    await this.init();
    if (this.pyBridge && this.pyBridge.saveAppConfig) {
      return await new Promise((res) => this.pyBridge.saveAppConfig(JSON.stringify(config), res));
    }
    return true;
  }

  public async getExecutiveReportText(params: any = {}): Promise<string> {
    await this.init();
    if (this.pyBridge && this.pyBridge.getExecutiveReportText) {
      const resStr: string = await new Promise((res) => this.pyBridge.getExecutiveReportText(JSON.stringify(params), res));
      const res = JSON.parse(resStr);
      return res.text || "";
    }
    return (
      "Kính gửi PGĐ @NAN PGĐ A THẮNG , TP @A Sơnpb1 TPKT NAN , TTH!\n\n" +
      "PVHKT kính gửi tiến độ cắt tồn wo tháng 9\ntheo PGNV của Đ/c PGĐCN đến ngày 28/9\n\n" +
      "+Thực hiện ngày: 31 WO\n\n" +
      "- Tổng tồn: 1008 Wo, trong đó:\n" +
      "178 Wo tồn quá hạn,\n" +
      "1 Wo tồn >30 ngày (MXN:1)\n\n" +
      "- Tồn cao tại TT: QLU, DDG, VPU, KLN, YTH\n\n" +
      "Kính đề nghị TTH tồn wo:\n\n" +
      "Đóng Wo quá hạn trước 30/9.\nĐóng hết wo tháng 9 xong trước 05/10.\n\n" +
      "@mọi người"
    );
  }

  public async getCenterDetails(centerCode: string): Promise<any> {
    await this.init();
    if (this.pyBridge && this.pyBridge.getCenterDetails) {
      const resStr: string = await new Promise((res) => this.pyBridge.getCenterDetails(centerCode, res));
      return JSON.parse(resStr);
    }
    return {
      code: centerCode,
      name: "Quỳnh Lưu",
      notification: `FT tồn quá hạn wo đến ngày hôm nay 28/9, khẩn trương hoàn thành trước 05/10. FT không có tiến độ ngày sẽ triệu tập họp vào 06:30 ngày mai @Đinh Xuân Hương @Nguyễn Văn Nam`,
      subtotal: { ton: 145, qua_han: 22, qua_han_30: 0, thuc_hien_ngay: 5 },
      employees: [
        {
          row_idx: 4,
          username: "huongdx3",
          full_name: "Đinh Xuân Hương",
          position: "NV DM",
          center_code: centerCode,
          ton: 2,
          qua_han: 1,
          qua_han_30: 0,
          thuc_hien_ngay: 0,
          should_tag: true,
          is_tagged: true,
          icms_bd_nt_ton: 0,
          icms_bd_nt_qh: 0,
          icms_bd_nt_qh30: 0,
          icms_bd_thc_ton: 1,
          icms_bd_thc_qh: 1,
          icms_bd_thc_qh30: 0,
          icms_tt_tc_ton: 0,
          icms_tt_tc_qh: 0,
          icms_tt_tc_qh30: 0,
          bao_hong_ton: 1,
          bao_hong_qh: 0,
          bao_hong_qh30: 0
        }
      ],
      overdue_wos_count: 14,
      pending_wos_count: 128
    };
  }

  public async setEmployeeTag(centerCode: string, username: string, isTagged: boolean): Promise<boolean> {
    await this.init();
    if (this.pyBridge && this.pyBridge.setEmployeeTag) {
      return await new Promise((res) => this.pyBridge.setEmployeeTag(centerCode, username, isTagged, res));
    }
    return true;
  }

  public async queryWorkOrders(params: any): Promise<{ total: number; page: number; page_size: number; total_pages: number; items: WorkOrderItem[] }> {
    await this.init();
    if (this.pyBridge && this.pyBridge.queryWorkOrders) {
      const resStr: string = await new Promise((res) => this.pyBridge.queryWorkOrders(JSON.stringify(params), res));
      return JSON.parse(resStr);
    }
    return {
      total: 1039,
      page: 1,
      page_size: 50,
      total_pages: 21,
      items: [
        {
          stt: 1,
          code: "WO_ICMS_20260827_0001",
          job_type: "ICMS_Bảo dưỡng nhà trạm",
          content: "Bảo dưỡng định kỳ trạm NAN0101",
          deadline: "28/09/2026 17:00:00",
          status: "FT Đang thực hiện",
          performer: "huongdx3",
          station_code: "NAN0101",
          ft_comment: "",
          ft_mobile: "0981234567",
          completed_date: "",
          overdue_days: -2,
          center_code: "QLU",
          center_name: "Quỳnh Lưu",
          bkk: "",
          bkk_reason: "",
          classification: "overdue"
        }
      ]
    };
  }

  public async copyToClipboard(actionType: string, params: any = {}): Promise<boolean> {
    await this.init();
    if (this.pyBridge && this.pyBridge.copyToClipboard) {
      return await new Promise((res) => this.pyBridge.copyToClipboard(actionType, JSON.stringify(params), res));
    }
    // Web clipboard fallback
    if (navigator.clipboard) {
      const text = params.text || params.notification || "Copied to clipboard";
      await navigator.clipboard.writeText(text);
      return true;
    }
    return false;
  }

  public async copyCustomHtmlAndText(text: string, html: string): Promise<boolean> {
    await this.init();
    if (this.pyBridge && this.pyBridge.copyCustomHtmlAndText) {
      return await new Promise((res) => this.pyBridge.copyCustomHtmlAndText(text, html, res));
    }
    if (navigator.clipboard) {
      try {
        const textBlob = new Blob([text], { type: "text/plain" });
        const htmlBlob = new Blob([html], { type: "text/html" });
        await navigator.clipboard.write([
          new ClipboardItem({
            "text/plain": textBlob,
            "text/html": htmlBlob
          })
        ]);
        return true;
      } catch {
        await navigator.clipboard.writeText(text);
        return true;
      }
    }
    return false;
  }

  public async copyImageFromBase64(base64Str: string): Promise<boolean> {
    await this.init();
    if (this.pyBridge && this.pyBridge.copyImageFromBase64) {
      return await new Promise((res) => this.pyBridge.copyImageFromBase64(base64Str, res));
    }
    if (navigator.clipboard && typeof ClipboardItem !== "undefined") {
      try {
        let cleanBase64 = base64Str;
        if (cleanBase64.includes(",")) {
          cleanBase64 = cleanBase64.split(",")[1];
        }
        const byteCharacters = atob(cleanBase64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: "image/png" });
        await navigator.clipboard.write([new ClipboardItem({ "image/png": blob })]);
        return true;
      } catch (e) {
        console.warn("Web image clipboard fallback failed:", e);
      }
    }
    return false;
  }

  public async getExcelSheetNames(filePath: string): Promise<{ success: boolean; sheets: string[]; error?: string }> {
    await this.init();
    if (this.pyBridge && this.pyBridge.getExcelSheetNames) {
      const resStr: string = await new Promise((res) => this.pyBridge.getExcelSheetNames(filePath, res));
      return JSON.parse(resStr);
    }
    return {
      success: true,
      sheets: ["DCU", "DDG", "KLN", "MXN", "NLC", "QPG", "QLU", "QHP", "TKY", "THU", "VPU", "VTG", "TDG", "YTH"]
    };
  }

  public async parseExcelRange(filePath: string, sheetName: string, rangeStr: string): Promise<{ success: boolean; data?: any; error?: string }> {
    await this.init();
    if (this.pyBridge && this.pyBridge.parseExcelRange) {
      const resStr: string = await new Promise((res) => this.pyBridge.parseExcelRange(filePath, sheetName, rangeStr, res));
      return JSON.parse(resStr);
    }
    return {
      success: true,
      data: {
        sheet_name: sheetName,
        range_str: rangeStr || "A1:H20",
        total_rows: 20,
        total_cols: 8,
        preview_rows: [],
        html_table: "<table border='1'><tr><td>Sample Table</td></tr></table>",
        tsv_text: "Sample Table",
        plain_text: "Sample Table"
      }
    };
  }

  public async copyExcelRange(filePath: string, sheetName: string, rangeStr: string, copyMode: "html" | "tsv" | "text"): Promise<boolean> {
    await this.init();
    if (this.pyBridge && this.pyBridge.copyExcelRange) {
      return await new Promise((res) => this.pyBridge.copyExcelRange(filePath, sheetName, rangeStr, copyMode, res));
    }
    return true;
  }

  public async openFile(filePath: string): Promise<boolean> {
    await this.init();
    if (this.pyBridge && this.pyBridge.openFile) {
      return await new Promise((res) => this.pyBridge.openFile(filePath, res));
    }
    console.log("[Bridge Mock] openFile:", filePath);
    return true;
  }

  public async openFolder(folderPath: string): Promise<boolean> {
    await this.init();
    if (this.pyBridge && this.pyBridge.openFolder) {
      return await new Promise((res) => this.pyBridge.openFolder(folderPath, res));
    }
    console.log("[Bridge Mock] openFolder:", folderPath);
    return true;
  }

  public async exportReport(exportType: string, params: any = {}): Promise<{ success: boolean; output_path?: string; output_paths?: string[]; error?: string }> {
    await this.init();
    if (this.pyBridge && this.pyBridge.exportReport) {
      const resStr: string = await new Promise((res) => this.pyBridge.exportReport(exportType, JSON.stringify(params), res));
      return JSON.parse(resStr);
    }
    return { success: true, output_path: "C:\\Reports\\BaoCao_Mock.xlsx" };
  }

  public async getReportHistory(limit = 50, offset = 0, type = ""): Promise<ReportHistoryItem[]> {
    await this.init();
    if (this.pyBridge && this.pyBridge.getReportHistory) {
      const resStr: string = await new Promise((res) => this.pyBridge.getReportHistory(limit, offset, type, res));
      return JSON.parse(resStr);
    }
    return [];
  }

  public async deleteReportHistory(id: number): Promise<boolean> {
    await this.init();
    if (this.pyBridge && this.pyBridge.deleteReportHistory) {
      return await new Promise((res) => this.pyBridge.deleteReportHistory(id, res));
    }
    return true;
  }

  public async getTemplates(type = ""): Promise<any[]> {
    await this.init();
    if (this.pyBridge && this.pyBridge.getTemplates) {
      const resStr: string = await new Promise((res) => this.pyBridge.getTemplates(type, res));
      return JSON.parse(resStr);
    }
    return [];
  }

  public async saveTemplate(name: string, type: string, content: string, placeholders = "", isDefault = false): Promise<number> {
    await this.init();
    if (this.pyBridge && this.pyBridge.saveTemplate) {
      return await new Promise((res) => this.pyBridge.saveTemplate(name, type, content, placeholders, isDefault, res));
    }
    return 1;
  }

  private getMockDataset(): DatasetSummary {
    const centersList: CenterOverview[] = [
      { code: "QLU", name: "Quỳnh Lưu", full_name: "Trung tâm Quỳnh Lưu (VCC_NAN_007_QLU)", total_employees: 25, tagged_employees: 18, overdue_wos: 14, pending_wos: 128, boundary_wos: 3, tong_ton: 145, ton_qua_han: 14, ton_30_ngay: 0, thuc_hien_ngay: 5, kh_ngay: 6, ty_le_ht_ngay: 0.83, danh_gia: "Đạt", hop_ngay: "Có" },
      { code: "DDG", name: "Đô Lương", full_name: "Trung tâm Đô Lương (VCC_NAN_011_DDG)", total_employees: 22, tagged_employees: 17, overdue_wos: 16, pending_wos: 110, boundary_wos: 2, tong_ton: 128, ton_qua_han: 16, ton_30_ngay: 0, thuc_hien_ngay: 4, kh_ngay: 5, ty_le_ht_ngay: 0.80, danh_gia: "Đạt", hop_ngay: "Có" },
      { code: "VPU", name: "Vinh Phú", full_name: "Trung tâm Vinh Phú (VCC_NAN_001_VPU)", total_employees: 30, tagged_employees: 24, overdue_wos: 22, pending_wos: 91, boundary_wos: 5, tong_ton: 118, ton_qua_han: 22, ton_30_ngay: 0, thuc_hien_ngay: 3, kh_ngay: 6, ty_le_ht_ngay: 0.50, danh_gia: "Chưa đạt", hop_ngay: "Có" },
      { code: "KLN", name: "Kim Liên", full_name: "Trung tâm Kim Liên (VCC_NAN_002_KLN)", total_employees: 18, tagged_employees: 14, overdue_wos: 15, pending_wos: 85, boundary_wos: 2, tong_ton: 102, ton_qua_han: 15, ton_30_ngay: 0, thuc_hien_ngay: 3, kh_ngay: 4, ty_le_ht_ngay: 0.75, danh_gia: "Đạt", hop_ngay: "Có" },
      { code: "YTH", name: "Yên Thành", full_name: "Trung tâm Yên Thành (VCC_NAN_005_YTH)", total_employees: 23, tagged_employees: 19, overdue_wos: 18, pending_wos: 82, boundary_wos: 4, tong_ton: 104, ton_qua_han: 18, ton_30_ngay: 0, thuc_hien_ngay: 2, kh_ngay: 5, ty_le_ht_ngay: 0.40, danh_gia: "Chưa đạt", hop_ngay: "Có" },
      { code: "DCU", name: "Diễn Châu", full_name: "Trung tâm Diễn Châu (VCC_NAN_004_DCU)", total_employees: 19, tagged_employees: 15, overdue_wos: 11, pending_wos: 46, boundary_wos: 1, tong_ton: 58, ton_qua_han: 11, ton_30_ngay: 0, thuc_hien_ngay: 2, kh_ngay: 3, ty_le_ht_ngay: 0.67, danh_gia: "Đạt", hop_ngay: "Có" },
      { code: "MXN", name: "Mường Xén", full_name: "Trung tâm Mường Xén (VCC_NAN_014_MXN)", total_employees: 10, tagged_employees: 8, overdue_wos: 9, pending_wos: 28, boundary_wos: 1, tong_ton: 38, ton_qua_han: 9, ton_30_ngay: 1, thuc_hien_ngay: 1, kh_ngay: 2, ty_le_ht_ngay: 0.50, danh_gia: "Chưa đạt", hop_ngay: "Có" }
    ];

    return {
      file_path: "samples/ĐH WO UT1 (05102026).xlsx",
      file_fingerprint: "a9f3b14c7e2890d6",
      detected_sheets: ["TH TTH", "THFT", "WO", "Sheet2", "Logfile"],
      report_date_str: "28/09/2026",
      day_month_str: "28/9",
      deadline_str: "05/10",
      meeting_time_str: "06:30",
      total_employees: 229,
      total_tagged: 182,
      total_work_orders: 178,
      total_pending_work_orders: 829,
      total_boundary_work_orders: 32,
      province_summary: {
        day: 28,
        month: 9,
        year: 2026,
        thuc_hien_ngay: 31,
        tong_ton: 1008,
        ton_qua_han: 178,
        ton_tren_30_ngay: 1,
        top_centers: ["QLU", "DDG", "VPU", "KLN", "YTH"],
        overdue_30_centers: [["MXN", 1]],
        has_discrepancy: false,
        discrepancy_details: ""
      },
      centers: centersList
    };
  }
}

export const bridge = new BridgeService();
