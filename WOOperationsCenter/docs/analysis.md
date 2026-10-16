# BÁO CÁO PHÂN TÍCH KIẾN TRÚC VÀ KẾ HOẠCH HỢP NHẤT
# WO OPERATIONS CENTER

> **Phiên bản:** 1.0.0  
> **Tác giả:** Senior Software Architect & Engineering Team  
> **Ngày lập:** 16/10/2026  
> **Mục tiêu:** Hợp nhất `wo_report_tool` và `THFTReportTool` thành hệ thống điều hành tập trung duy nhất: **WO Operations Center**.

---

## 1. TỔNG QUAN HIỆN TRẠNG HAI ỨNG DỤNG NGUỒN

### 1.1. Ứng dụng A — WO Reporting (`wo_report_tool`)
- **Mục đích:** Đọc dữ liệu tiến độ điều hành từ sheet `TH TTH` (Tổng hợp Trung tâm Huyện), tính toán các chỉ số cắt tồn toàn tỉnh, sinh bản tin thông báo điều hành theo mẫu chuẩn Word gửi qua TAMMI và xuất báo cáo Excel 2 sheet (`BaoCao` và `ChiTiet`).
- **Nguồn dữ liệu chính:**
  - Sheet `TH TTH`: Dòng 3 là dòng Tổng cộng toàn tỉnh; Dòng 4..17 là 14 Trung tâm Huyện.
  - Cột trích xuất:
    - Cột A: Tên trung tâm (kèm mã rút gọn trong ngoặc đơn, VD: `Trung tâm Quỳnh Lưu (VCC_NAN_007_QLU)`)
    - Cột Q: Tổng tồn (1008)
    - Cột R: Tồn quá hạn (178)
    - Cột S: Tồn >30 ngày (1, tại MXN)
    - Cột T: Thực hiện ngày (31)
    - Cột U: KH Ngày
    - Cột V: Đánh giá
    - Cột W: Họp ngày
    - Cột X: Tỷ lệ HT ngày
- **Điểm mạnh:**
  - Logic trích xuất nhanh, có cơ chế fallback tính tổng các huyện con nếu ô công thức dòng 3 chưa cache.
  - Sinh tin nhắn TAMMI gọn gàng, định dạng danh sách >30 ngày theo cú pháp `(MXN:1)`.
  - Xuất Excel có định dạng tiêu đề, Freeze Panes, AutoFilter.
- **Hạn chế & Nợ kỹ thuật:**
  - Chỉ tập trung vào sheet `TH TTH`, hoàn toàn bỏ qua dữ liệu nhân viên FT (`THFT`) và danh sách công việc chi tiết (`WO`).
  - Giao diện PySide6 thuần (QWidgets) đơn điệu, không có biểu đồ trực quan, không có Dark mode.
  - Không lưu lịch sử báo cáo, không quản lý được mẫu thông báo động.

### 1.2. Ứng dụng B — THFT Reporting (`THFTReportTool`)
- **Mục đích:** Đọc dữ liệu từ sheet `THFT` và `WO`, phân nhóm theo 14 Trung tâm Huyện, tính toán gắn thẻ (TAG) nhân viên theo quy tắc nghiệp vụ, lọc theo vị trí (`NV DM`, `NV NHÀ TRẠM`), phân loại danh sách WO quá hạn (< 0 ngày) và WO tồn chưa quá hạn (> 0 ngày), hỗ trợ copy Clipboard HTML/Text và xuất Excel đa worksheet (mỗi huyện 1 sheet).
- **Nguồn dữ liệu chính:**
  - Sheet `THFT`: 241 dòng (229 nhân viên FT, 167 NV DM, 58 NV Nhà Trạm).
  - Sheet `WO`: 1040 dòng (1039 WO, 178 WO quá hạn, 829 WO trong hạn, 32 bản ghi biên/0 ngày/trống).
  - Sheet `TH TTH`: Chỉ dùng để đọc thời điểm ngày báo cáo (ô Y2, AA2).
- **Điểm mạnh:**
  - Logic phân loại nghiệp vụ chặt chẽ, có bộ test tự động 19 kịch bản (`test_all.py`).
  - Hỗ trợ xuất Clipboard HTML Table cho TAMMI / Teams / Word giữ nguyên màu sắc Word chuẩn.
  - Phân loại rõ ràng 2 bảng WO quá hạn (Navy Blue) và WO trong hạn (Forest Green) ngay dưới bảng nhân viên.
- **Hạn chế & Nợ kỹ thuật:**
  - Bỏ sót 32 bản ghi WO ở trạng thái biên (cột L = 0 hoặc rỗng) do chỉ lọc `< 0` và `> 0`.
  - Chưa tận dụng số liệu điều hành toàn tỉnh ở sheet `TH TTH` (chỉ lấy ngày).
  - Mã nguồn xuất Excel lặp lại nhiều khối định dạng giữa các sheet huyện, gây chậm khi xuất file lớn.
  - Giao diện PySide6 thuần kích thước cố định, nhiều nút bấm dàn trải, thiếu tính đồng bộ và trải nghiệm người dùng cao cấp.

---

## 2. PHÂN TÍCH TỆP DỮ LIỆU MẪU THỰC TẾ

Phân tích trực tiếp tệp `ĐH WO UT1 (05102026).xlsx` (kích thước ~28 MB):
1. **Các worksheet hiện diện:**
   - `TH TTH`: 1,052 dòng (14 huyện dữ liệu thực, dòng 3 là tổng cộng).
   - `THFT`: 241 dòng (229 nhân viên FT).
   - `WO`: 1,040 dòng (1,039 công việc WO).
   - `Logfile`: 376,891 dòng (Nhật ký giao dịch hệ thống cực lớn!).
   - `Sheet2`: 24 dòng (Thống kê mã trạm và số lượng).
2. **Nguy cơ cạn kiệt bộ nhớ từ sheet `Logfile`:**
   - Với hơn 376,000 dòng, nếu đọc toàn bộ workbook bằng `openpyxl` ở chế độ thông thường hoặc đẩy sang giao diện web, ứng dụng sẽ bị tràn RAM (OutOfMemory) hoặc đơ giao diện 10-30 giây.
   - **Giải pháp:** Chỉ nạp các sheet mục tiêu (`TH TTH`, `THFT`, `WO`, `Sheet2`). Tuyệt đối bỏ qua hoặc đọc streaming theo yêu cầu đối với `Logfile`.
3. **Sự không nhất quán về cấu trúc cột giữa các phiên bản file mẫu:**
   - Phiên bản 1 (`THFTReportTool/samples/ĐH WO UT1 (05102026) (1).xlsx`): Có cột B là `Tên FT` (20 cột A..T).
   - Phiên bản 2 (`wo_report_tool/samples/ĐH WO UT1 (05102026).xlsx`): Không có cột `Tên FT`, cột B là `TTH`, cột C là `Vị trí`, cột P là `Tổng Tồn` (19 cột).
   - **Giải pháp:** Bộ máy `ExcelInputEngine` phải nhận diện tiêu đề động (Dynamic Header Detection) dựa trên từ khóa: `FT`, `Tên FT` / `Họ và tên`, `TTH` / `Trung tâm`, `Vị trí`, `Tổng - Tồn`, `Quá hạn`, `Thực hiện ngày`.

---

## 3. ĐỐI CHIẾU VÀ HỢP NHẤT QUY TẮC NGHIỆP VỤ

| Quy tắc nghiệp vụ | Ứng dụng nguồn | Quy tắc hợp nhất trong WO Operations Center |
| :--- | :--- | :--- |
| **Nhận diện ngày báo cáo** | `TH TTH` (Y2, AA2) hoặc tên file | Đọc ưu tiên ô Y2/AA2 từ `TH TTH`, fallback sang tên file regex `(\d{8}|\d{6})`, fallback sang ngày hiện tại; cho phép người dùng sửa trực tiếp trên Top Bar. |
| **Đối soát số liệu toàn tỉnh** | `TH TTH` dòng 3 vs tổng chi tiết | Đối chiếu giá trị `Q3`, `R3`, `S3`, `T3` với tổng cộng của 14 huyện (`Q4:Q17`, `R4:R17`, ...). Nếu có sai lệch, hiển thị cảnh báo Discrepancy Warning thay vì tự ý sửa đổi. |
| **Top 5 tồn cao** | `wo_report_tool` | Lấy 5 trung tâm có tổng tồn lớn nhất, trích xuất mã 3 ký tự (VD: `QLU, DDG, VPU, KLN, YTH`). |
| **Tồn > 30 ngày** | `wo_report_tool` | Liệt kê mã huyện và số lượng: `(MXN:1)`. |
| **Điều kiện gắn TAG nhân viên** | `THFTReportTool` | `ton > 0 AND thuc_hien_ngay <= 0` (giá trị rỗng xem như 0). Không tag khi `ton == 0` hoặc `thuc_hien_ngay > 0`. |
| **Ghi đè TAG thủ công** | `THFTReportTool` | Cho phép người dùng bật/tắt checkbox TAG từng nhân viên; lưu trạng thái override và cập nhật tức thì vào bản tin, clipboard và file xuất. |
| **Định dạng Token TAG** | Cả hai | Hỗ trợ 4 định dạng: `@Họ và tên`, `@HỌ VÀ TÊN`, `@username`, `@FT username`, tùy biến theo từng huyện. |
| **Phân loại WO** | `THFTReportTool` | Cột L < 0: Quá hạn; Cột L > 0: Tồn trong hạn; Cột L == 0 hoặc Blank: Trạng thái biên/chưa xác định (hiển thị riêng, không bỏ sót). |
| **Bảo toàn dữ liệu nguồn** | Cả hai | Mở workbook với cờ `read_only=True`, tuyệt đối không ghi đè file gốc. |

---

## 4. KIẾN TRÚC MỤC TIÊU: WO OPERATIONS CENTER

### 4.1. Ngăn xếp công nghệ (Technology Stack)
- **Host Desktop:** Python 3.12 + PySide6 (Qt WebEngine + Qt WebChannel / Local Secure IPC).
- **Engine tính toán & Excel:** Python (`openpyxl`, `python-docx`, SQLite, luồng nền `QThread`).
- **Giao diện người dùng:** React 18 + TypeScript + Vite + Tailwind CSS + Lucide Icons + TanStack Table + Recharts + Zustand.
- **Bộ nhận diện UI/UX:** Chuẩn `evondevKit` (Thiết kế dashboard phẳng, tối giản, chuyên nghiệp, hỗ trợ Light/Dark mode, bố cục responsive desktop, phím tắt, toast, skeleton).
- **Lưu trữ cục bộ:** SQLite tại thư mục `%APPDATA%\WOOperationsCenter` (lưu cấu hình, lịch sử báo cáo, mẫu template).
- **Đóng gói:** PyInstaller (.spec tối ưu tài nguyên WebEngine) + Inno Setup (.iss tạo bộ cài chuyên nghiệp).

### 4.2. Cấu trúc thư mục Monorepo chuẩn hóa
```text
WOOperationsCenter/
├── backend/
│   ├── core/
│   │   ├── config.py             # Cấu hình hệ thống, đường dẫn AppData
│   │   └── logging.py            # Ghi log tập trung có xoay vòng
│   ├── domain/
│   │   ├── models.py             # Data models chuẩn hóa (ReportDataset, Center, Employee, WO...)
│   │   └── validation.py         # Quy tắc xác thực tính toàn vẹn số liệu
│   ├── readers/
│   │   └── excel_input_engine.py # Đọc Excel tối ưu, nhận diện sheet/cột động, streaming
│   ├── processors/
│   │   ├── executive_report.py   # Xử lý báo cáo điều hành tỉnh
│   │   ├── thft_report.py        # Xử lý báo cáo FT, tính tag, phân nhóm huyện
│   │   └── wo_explorer.py        # Tìm kiếm, lọc và phân trang dữ liệu WO
│   ├── exporters/
│   │   ├── excel_exporter.py     # Xuất Excel đa định dạng (WO & THFT)
│   │   └── docx_exporter.py      # Xuất Word theo mẫu chuẩn
│   ├── clipboard/
│   │   └── clipboard_engine.py   # Windows HTML Clipboard CF_HTML, TSV, Plain Text
│   ├── database/
│   │   └── repository.py         # Quản lý SQLite (Lịch sử báo cáo, cài đặt, template)
│   ├── bridge/
│   │   └── api_bridge.py         # Cầu nối an toàn giữa React và Python Engine
│   └── workers/
│       └── async_tasks.py        # Worker luồng nền phục vụ import/export
├── frontend/
│   ├── src/
│   │   ├── app/                  # App shell, routing
│   │   ├── layouts/              # MainLayout, Sidebar, TopBar
│   │   ├── pages/                # Tổng quan, Nhập liệu, Điều hành WO, THFT, WO Explorer...
│   │   ├── components/           # UI kit chuẩn evondevKit (Card, Button, Table, Modal...)
│   │   ├── stores/               # Zustand state stores
│   │   └── services/             # API client giao tiếp với Python bridge
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── tests/
│   ├── test_domain.py            # Kiểm thử domain models
│   ├── test_excel_reader.py      # Kiểm thử đọc Excel động
│   ├── test_tagging_rules.py     # Kiểm thử 100% quy tắc TAG nhân viên
│   ├── test_regression.py        # Kiểm thử hồi quy đối chiếu kết quả cũ
│   └── test_clipboard.py         # Kiểm thử Windows CF_HTML
├── packaging/
│   ├── WOOperationsCenter.spec   # Cấu hình PyInstaller
│   └── setup_installer.iss       # Kịch bản Inno Setup 6
├── main.py                       # Điểm khởi chạy ứng dụng chính
└── requirements.txt
```

---

## 5. KẾ HOẠCH TRIỂN KHAI THEO GIAI ĐOẠN

1. **Giai đoạn 1 — Audit & Foundation:** Hoàn thành báo cáo phân tích, chuẩn bị môi trường và thư viện.
2. **Giai đoạn 2 — Shared Domain & Python Processing Engine:** Xây dựng core domain models, Excel reader thông minh, các processor nghiệp vụ cho WO và THFT, bộ quản lý SQLite và clipboard CF_HTML.
3. **Giai đoạn 3 — Design System & Frontend Setup:** Cài đặt React + Vite + Tailwind, tích hợp bộ tokens `evondevKit`, xây dựng trang `/design-system` và các thành phần cốt lõi.
4. **Giai đoạn 4 — Application Shell & IPC Bridge:** Xây dựng cửa sổ chính PySide6, nhúng WebEngine với cầu nối bridge an toàn, thiết lập cơ chế nạp dataset dùng chung.
5. **Giai đoạn 5 — Feature Migration:** Dựng hoàn chỉnh 9 màn hình theo yêu cầu nghiệp vụ: Tổng quan, Nhập dữ liệu, Báo cáo điều hành WO, Báo cáo nhân viên FT, Danh sách công việc WO, Trung tâm huyện, Soạn thông báo, Lịch sử báo cáo, Cài đặt.
6. **Giai đoạn 6 — Regression Testing:** Chạy kiểm thử tự động toàn diện với file dữ liệu mẫu thực tế, so sánh khớp 100% kết quả cũ.
7. **Giai đoạn 7 — Packaging & Verification:** Biên dịch bundle production frontend, đóng gói PyInstaller EXE và kịch bản Inno Setup.
