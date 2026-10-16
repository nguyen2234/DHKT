# WO OPERATIONS CENTER — TRUNG TÂM ĐIỀU HÀNH WO

> **Phiên bản:** 1.0.0 Production Ready  
> **Đơn vị phát triển:** Phòng VHKT — NAN_DHKT  
> **Nền tảng:** Windows 10/11 x64 (Hoạt động 100% Offline)  
> **Ngôn ngữ giao diện:** Tiếng Việt Unicode 100%

---

## 🌟 GIỚI THIỆU TỔNG QUAN

**WO Operations Center** là hệ thống phần mềm máy tính để bàn (Windows Desktop Application) hợp nhất toàn diện hai công cụ báo cáo tiền nhiệm (`wo_report_tool` và `THFTReportTool`) thành một trung tâm điều hành tập trung, hiện đại và chuẩn mực cao cấp.

Ứng dụng kết hợp sức mạnh xử lý số liệu lớn, streaming đa luồng của **Python 3.12** cùng giao diện người dùng tương tác cao cấp của **React 18 + TypeScript + Tailwind CSS** chạy trên nền tảng **Qt WebEngine** thông qua cầu nối an toàn cục bộ (Local Secure Bridge).

---

## 🚀 TÍNH NĂNG NỔI BẬT THEO CÁC PHÂN HỆ

### 1. Phân hệ A — Báo cáo Điều hành WO Toàn tỉnh (Executive Report)
- Tự động trích xuất các chỉ số điều hành cốt lõi từ sheet `TH TTH`:
  - **Thực hiện ngày**: Cột T (dòng 3).
  - **Tổng tồn**: Cột Q (dòng 3).
  - **Tồn quá hạn**: Cột R (dòng 3).
  - **Tồn > 30 ngày**: Cột S (dòng 3), tự động liệt kê chi tiết các huyện có tồn >30 ngày theo cú pháp `(MXN:1, TDG:1)`.
  - **Top 5 trung tâm tồn cao**: Sắp xếp giảm dần theo tổng tồn, tự động trích xuất mã 3 ký tự (VD: `QLU, DDG, VPU, KLN, YTH`).
- Cơ chế đối soát tổng hợp (Summary Reconciliation): Tự động so sánh số liệu dòng 3 với tổng cộng thực tế của 14 huyện con. Cảnh báo sai lệch minh bạch nếu có chênh lệch.
- Cho phép chỉnh sửa trực tiếp ngày báo cáo, người nhận, các mốc thời hạn (deadline) và nội dung thông báo.
- Sao chép 1-click lên nhóm chat **TAMMI** với văn bản thuần Unicode sạch.
- Xuất file Excel báo cáo định dạng chuyên nghiệp với 2 worksheet:
  - Sheet `BaoCao`: Bảng tổng hợp chỉ số nổi bật, khung thông báo gửi TAMMI.
  - Sheet `ChiTiet`: Toàn bộ 14 trung tâm huyện với Freeze Panes, AutoFilter và hàng tổng cộng.

### 2. Phân hệ B — Báo cáo Nhân viên Kỹ thuật FT (THFT Reporting)
- Phân nhóm tự động toàn bộ 229 nhân viên FT theo 14 Trung tâm Huyện độc lập.
- Bộ lọc chức danh nghiệp vụ tương tác:
  - **Tất cả vị trí** (229 FT)
  - **Nhân viên Dây máy (NV DM)** (167 FT)
  - **Nhân viên Nhà trạm (NV NHÀ TRẠM)** (58 FT)
- **Quy tắc gắn TAG nhân viên tự động tuyệt đối chuẩn xác**:
  $$\text{should\_tag} = (\text{Tổng tồn } Q > 0) \land (\text{Thực hiện ngày } T \le 0 \lor T \text{ rỗng})$$
  - Không tag khi nhân viên có tồn $Q = 0$ hoặc đã có tiến độ trong ngày ($T > 0$).
  - Cho phép người dùng bật/tắt thủ công (Manual Override) checkbox TAG cho từng nhân sự.
- **Tính độc lập từng huyện**: Báo cáo huyện nào chỉ gắn tag nhân viên thuộc huyện đó, tuyệt đối không lẫn lộn nhân sự giữa các huyện.
- Hỗ trợ đa dạng định dạng thẻ tag: `@Họ và tên`, `@HỌ VÀ TÊN`, `@username`, `@FT username`, `@username VịTrí Huyện`.
- Sao chép đồng thời định dạng **HTML Table** (chuẩn màu Word) và **Plain Text / TSV** cho Clipboard Windows.

### 3. Phân hệ C — Danh mục & Tra cứu Công việc WO (Work Order Explorer)
- Khai thác trọn vẹn dữ liệu từ sheet `WO` với đầy đủ 15 cột thông tin nghiệp vụ.
- **Phân loại 3 trạng thái công việc**:
  - Cột L $< 0$: WO Quá hạn (Overdue)
  - Cột L $> 0$: WO Tồn trong hạn (Pending)
  - Cột L $= 0$ hoặc rỗng: Trạng thái biên / Chưa xác định (không bị bỏ sót).
- Tìm kiếm toàn văn (Full-text Search): Theo mã WO, họ tên nhân viên, mã trạm, nội dung công việc, số điện thoại, ghi chú.
- Bộ lọc kết hợp: Theo huyện, loại công việc, trạng thái xử lý, phân loại quá hạn.
- Phân trang dữ liệu mượt mà, hỗ trợ copy nhanh dạng bảng TSV để dán trực tiếp vào Excel.
- Hộp thoại (Modal) xem chi tiết từng công việc, bao gồm thông tin Bất khả kháng (BKK) và lý do BKK.

### 4. Phân hệ D — Không gian Làm việc theo Trung tâm Huyện (Center Management)
- Bảng điều khiển danh mục 14 Trung tâm Huyện với đầy đủ thẻ chỉ số: Tổng tồn, Quá hạn, Tồn >30N, Thực hiện ngày, Số lượng FT và Số FT cần TAG.
- Bấm vào từng huyện để mở không gian làm việc chi tiết:
  - Tab Báo cáo Nhân sự FT & TAG.
  - Tab Danh sách WO Quá hạn (Bảng Navy Blue).
  - Tab Danh sách WO Tồn trong hạn (Bảng Forest Green).
- Hỗ trợ xuất độc lập file Excel và file Word (.docx) cho từng huyện riêng biệt.

### 5. Phân hệ E — Soạn thảo & Tùy biến Báo cáo (Report Builder)
- Trình soạn thảo mẫu báo cáo trực quan với cơ chế thế chỗ an toàn (Deterministic Placeholder Substitution):
  - `{NGAY_BAO_CAO}`, `{THANG}`, `{NAM}`, `{TONG_TON}`, `{TON_QUA_HAN}`, `{TON_TREN_30_NGAY}`, `{CHI_TIET_TREN_30_NGAY}`, `{TOP_5_TRUNG_TAM}`, `{THUC_HIEN_NGAY}`, `{TEN_HUYEN}`, `{MA_HUYEN}`, `{DANH_SACH_TAG}`, `{HAN_HOAN_THANH}`, `{GIO_HOP}`.
  - Tự động phát hiện và cảnh báo các placeholder không hợp lệ.
  - Khung xem trước trực tiếp (Live Preview) cập nhật số liệu theo thời gian thực.
  - Lưu trữ các mẫu template tùy chỉnh vào SQLite.

### 6. Phân hệ F — Lịch sử & Cài đặt Hệ thống (History & Settings)
- **Lịch sử báo cáo**: Tự động lưu vết siêu dữ liệu các lần xuất báo cáo (ID, thời gian, loại báo cáo, ngày báo cáo, bộ lọc, đường dẫn file xuất) vào cơ sở dữ liệu SQLite tại `%APPDATA%\WOOperationsCenter\wo_operations.db`.
- **Cài đặt**:
  - Chuyển đổi giao diện Sáng / Tối (Light / Dark mode).
  - Tùy chọn thư mục xuất báo cáo mặc định.
  - Cấu hình người nhận mặc định và mốc thời hạn.
  - Quản lý cấu hình mapping cột Excel.

### 7. Hệ thống Thiết kế Giao diện (Design System — evondevKit)
- Ứng dụng tích hợp bộ Design Tokens chuẩn `evondevKit`:
  - Thiết kế phẳng (Flat Design), đường tóc mảnh, khoảng thở khoa học, tối giản và chuyên nghiệp.
  - Tuyệt đối không tạo cảm giác giao diện màu mè hay sinh ngẫu nhiên từ AI.
  - Trang `/design-system` trưng bày đầy đủ các thành phần: Nút bấm, Huy hiệu, Thẻ chỉ số, Hộp thoại modal, Bảng màu và Thang typography.

---

## 🛠 KIẾN TRÚC & CÔNG NGHỆ SỬ DỤNG

```text
WOOperationsCenter/
├── backend/
│   ├── core/                  # Cấu hình AppData, logging xoay vòng
│   ├── domain/                # Data models chuẩn hóa (ReportDataset, CenterReport...)
│   ├── readers/               # ExcelInputEngine (Streaming, nhận diện sheet/cột động)
│   ├── processors/            # ExecutiveReport, THFTReport, WOExplorer processors
│   ├── exporters/             # ExcelExporter (Màu chuẩn Word, 2 sub-tables), DocxExporter
│   ├── clipboard/             # Windows CF_HTML & Plain Text Clipboard Engine
│   ├── database/              # SQLite repository (Lịch sử báo cáo & templates)
│   └── bridge/                # Qt WebChannel / Local IPC Bridge an toàn
├── frontend/
│   ├── src/
│   │   ├── app/               # Ứng dụng chính & Router
│   │   ├── layouts/           # Sidebar, TopBar
│   │   ├── pages/             # 10 trang tính năng nghiệp vụ & /design-system
│   │   ├── components/ui/     # UI kit chuẩn evondevKit (Button, Card, Badge, Modal...)
│   │   ├── stores/            # Zustand state stores
│   │   └── services/          # Client bridge kết nối Python host
│   ├── package.json
│   └── vite.config.ts
├── tests/
│   └── test_all_operations.py # Bộ kiểm thử tự động 21/21 kịch bản nghiệp vụ
├── packaging/
│   ├── WOOperationsCenter.spec# Cấu hình PyInstaller
│   └── setup_installer.iss    # Kịch bản Inno Setup tạo bộ cài Windows Setup
├── scripts/
│   └── build_all.bat          # Kịch bản 1-click build toàn diện
├── main.py                    # Điểm khởi chạy ứng dụng chính
└── requirements.txt
```

---

## 📋 BẢNG MAPPING CỘT DỮ LIỆU TỪ EXCEL NGUỒN

### 1. Sheet `TH TTH` (Tổng hợp Trung tâm Huyện)
| Chỉ số | Tên cột / ô trong sheet | Cột Excel | Ghi chú |
| :--- | :--- | :--- | :--- |
| **Thực hiện ngày** | TH Ngày | Cột T (T3) | Lấy tại dòng 3 (Tổng cộng), đối soát với tổng huyện |
| **Tổng tồn** | Tồn (nhóm Điều hành UT1) | Cột Q (Q3) | Lấy tại dòng 3 |
| **Tồn quá hạn** | Tồn QH ngày | Cột R (R3) | Lấy tại dòng 3 |
| **Tồn >30 ngày** | Tồn QH >30 ngày | Cột S (S3) | Lấy tại dòng 3 |
| **Chi tiết >30 ngày** | Cột S từng dòng huyện | Cột S (S4..S17) | Định dạng: `(MXN:1)` |
| **Top 5 tồn cao** | Cột Q từng dòng huyện | Cột Q (Q4..Q17) | Sắp xếp giảm dần theo số lượng tồn |

### 2. Sheet `THFT` (Chi tiết Nhân viên Kỹ thuật)
| Cột | Tên cột | Ý nghĩa nghiệp vụ | Quy tắc xử lý |
| :---: | :--- | :--- | :--- |
| **A** | FT | Tài khoản / Username | Bắt buộc |
| **B** | Tên FT | Họ và tên nhân viên | Tự động nhận diện nếu có cột này |
| **C** | TTH | Trung tâm Huyện | Tách mã 3 ký tự và tên huyện |
| **D** | Vị trí | Chức danh | Hỗ trợ lọc `NV DM`, `NV NHÀ TRẠM` |
| **E–P**| Chi tiết nghiệp vụ | ICMS & Báo hỏng hạ tầng | Trích xuất số lượng tồn & quá hạn |
| **Q** | Tổng - Tồn | Tổng số lượng WO tồn | **Điều kiện 1 để TAG (Q > 0)** |
| **R** | Tổng - Quá hạn | Tổng tồn quá hạn | |
| **S** | Tổng - Quá hạn 30N | Tổng tồn quá hạn >30 ngày | |
| **T** | Thực hiện ngày | Tiến độ thực hiện ngày | **Điều kiện 2 để TAG (T <= 0)** |

### 3. Sheet `WO` (Danh mục Chi tiết Công việc)
| Cột | Tên cột | Ý nghĩa nghiệp vụ | Phân loại |
| :---: | :--- | :--- | :--- |
| **A..K** | Chi tiết công việc | Mã WO, loại việc, nội dung, hạn kết thúc, trạng thái, người thực hiện, mã trạm | Giữ nguyên 100% dữ liệu gốc |
| **L** | **Ngày quá hạn** | **Số ngày quá hạn / Còn lại** | **< 0: Quá hạn (Navy Blue)<br>> 0: Tồn trong hạn (Forest Green)<br>= 0 hoặc rỗng: Trạng thái biên** |
| **M..O** | TTH, BKK, Lý do | Trung tâm và lý do bất khả kháng | Giữ nguyên dữ liệu gốc |

---

## 💻 HƯỚNG DẪN CÀI ĐẶT & CHẠY TỪ SOURCE CODE

### 1. Yêu cầu môi trường
- Windows 10 hoặc Windows 11 (64-bit).
- Python 3.12 (đã cài đặt).
- Bun hoặc Node.js (phục vụ biên dịch frontend khi phát triển).

### 2. Cài đặt thư viện Python
Mở Terminal tại thư mục `WOOperationsCenter`:
```bash
pip install -r requirements.txt
```

### 3. Biên dịch React Frontend
```bash
cd frontend
bun install
bun run build
cd ..
```

### 4. Khởi chạy ứng dụng
- Chế độ sản xuất (đọc bundle offline):
  ```bash
  python main.py
  ```
- Chế độ phát triển (kết nối Vite dev server):
  ```bash
  # Terminal 1: Khởi chạy Vite dev server
  cd frontend && bun run dev

  # Terminal 2: Khởi chạy Python desktop host
  python main.py --dev
  ```

---

## 🧪 CHẠY BỘ KIỂM THỬ TỰ ĐỘNG

Chạy lệnh kiểm thử tự động toàn diện:
```bash
python tests/test_all_operations.py
```
Kết quả kiểm thử xác nhận đạt **21/21 kịch bản** (100% Passed):
- Nhận diện đúng cấu trúc workbook, sheets, và bảo toàn tệp nguồn read-only.
- Kiểm thử đầy đủ các điều kiện TAG tự động và ghi đè TAG thủ công.
- Kiểm thử lọc chức danh `NV DM` (167 FT) và `NV NHÀ TRẠM` (58 FT).
- Phân loại chính xác 3 trạng thái WO (<0, >0, biên).
- Kiểm tra toàn vẹn định dạng Windows CF_HTML clipboard và các tệp xuất Excel/Word.

---

## 📦 HƯỚNG DẪN ĐÓNG GÓI .EXE VÀ BỘ CÀI SETUP

Người dùng cuối **KHÔNG CẦN CÀI PYTHON, BUN HAY NODE.JS**.

### Cách 1: Sử dụng kịch bản 1-click (Khuyên dùng)
Nhấp đúp chuột vào file:
`WOOperationsCenter\scripts\build_all.bat`

Kịch bản sẽ tự động:
1. Biên dịch bundle React production tối ưu.
2. Đóng gói mã nguồn và thư viện thành thư mục thực thi `dist\WOOperationsCenter\WOOperationsCenter.exe`.
3. Tự động kiểm tra và biên dịch Inno Setup tạo file cài đặt `dist_installer\WOOperationsCenter_Setup.exe`.

### Cách 2: Đóng gói bằng PyInstaller thủ công
```bash
cd WOOperationsCenter
pyinstaller --clean -y packaging\WOOperationsCenter.spec
```

---

## 📖 HƯỚNG DẪN SỬ DỤNG CHO NGƯỜI DÙNG CUỐI

1. **Bước 1 — Nhập dữ liệu:**
   - Mở ứng dụng, vào tab **Nhập dữ liệu**.
   - Kéo thả file `ĐH WO UT1 (ddMMyyyy).xlsx` vào khung hoặc bấm "Chọn tệp từ máy tính".
   - Hệ thống tự động phân tích và chuyển sang **Bảng tổng quan**.
2. **Bước 2 — Báo cáo điều hành WO:**
   - Vào tab **Báo cáo điều hành WO**.
   - Kiểm tra các số liệu: Thực hiện ngày, Tổng tồn, Tồn quá hạn, Top 5 huyện.
   - Nhập hoặc sửa hạn chót hoàn thành (deadline) và nội dung thông báo.
   - Bấm **[Sao chép báo cáo]** để copy plain text vào Clipboard, sau đó mở TAMMI và nhấn `Ctrl + V`.
   - Bấm **[Xuất Excel]** nếu muốn lưu file `BaoCao_WO_YYYYMMDD.xlsx`.
3. **Bước 3 — Báo cáo Nhân viên FT:**
   - Vào tab **Báo cáo nhân viên FT**.
   - Chọn huyện cần báo cáo trên thanh chọn huyện.
   - Chọn bộ lọc vị trí: *Tất cả*, *NV DM*, hoặc *NV NHÀ TRẠM*.
   - Kiểm tra danh sách nhân viên cần TAG. Có thể bấm trực tiếp vào ô vuông checkbox đầu dòng để bật/tắt TAG thủ công cho bất kỳ nhân sự nào.
   - Bấm **[Copy Báo cáo Huyện]** để copy đồng thời bảng HTML màu chuẩn Word và Plain Text gửi TAMMI.
   - Bấm **[Xuất Excel Huyện]** để xuất file Excel chuẩn in A4 Landscape.
4. **Bước 4 — Tra cứu WO:**
   - Vào tab **Danh sách công việc WO**.
   - Nhập từ khóa tìm kiếm hoặc lọc theo huyện / phân loại quá hạn.
   - Bấm vào biểu tượng con mắt để xem đầy đủ thông tin chi tiết của từng WO.

---

## 🔒 AN TOÀN DỮ LIỆU & BẢO MẬT
- Hoạt động 100% Offline trên máy tính nội bộ.
- Không kết nối internet, không gọi API ngoài, không gửi dữ liệu ra bên ngoài.
- File nguồn Excel luôn được mở với cờ `read_only=True`, tuyệt đối không ghi đè, không làm mất công thức gốc.
- Mọi dữ liệu cài đặt và lịch sử báo cáo được lưu trữ độc lập tại thư mục người dùng `%APPDATA%\WOOperationsCenter`.
