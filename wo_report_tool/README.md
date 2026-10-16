# CÔNG CỤ TẠO BÁO CÁO WO (PHÒNG VHKT - NAN_DHKT)

Ứng dụng Windows Desktop hoàn chỉnh bằng Python và PySide6 giúp tự động đọc dữ liệu từ file Excel điều hành, tính toán các chỉ số tiến độ cắt tồn WO, sinh nội dung báo cáo chuẩn theo mẫu Word của đơn vị, hỗ trợ sao chép 1-click lên nhóm TAMMI và xuất file Excel báo cáo định dạng chuyên nghiệp.

---

## 🌟 TÍNH NĂNG NỔI BẬT

1. **Giao diện hiện đại, trực quan (PySide6)**:
   - Hỗ trợ tiếng Việt Unicode 100%.
   - Không bị treo giao diện (xử lý file lớn qua luồng nền `QThread`).
   - Tự động nhận diện file mẫu trong thư mục làm việc.
   - Thẻ thống kê trực quan (Thực hiện ngày, Tổng tồn, Tồn quá hạn, Tồn >30 ngày, Top 5 trung tâm).

2. **Logic trích xuất số liệu chuẩn xác**:
   - Tự động nhận diện sheet `TH TTH` (Tổng hợp trung tâm huyện).
   - Đọc chỉ số toàn tỉnh tại dòng tổng cộng (dòng 3):
     - **Thực hiện ngày**: Cột T (T3)
     - **Tổng tồn**: Cột Q (Q3)
     - **Tồn quá hạn**: Cột R (R3)
     - **Tồn >30 ngày**: Cột S (S3)
   - Tự động fallback tính tổng các huyện con nếu file chưa cache công thức Excel.
   - **Tồn >30 ngày**: Liệt kê chi tiết mã huyện có tồn >30 ngày (ví dụ `(MXN:1)`).
   - **Top 5 tồn cao**: Tự động trích xuất mã 3 ký tự (VPU, KLN, NLC, DCU, YTH, QLU, THU, QHP, QPG, TKY, DDG, VTG, TDG, MXN) và sắp xếp giảm dần theo số lượng tồn.
   - **Xem chi tiết 14 huyện**: Có nút mở bảng xem trực tiếp toàn bộ dữ liệu 14 trung tâm huyện.

3. **Chỉnh sửa linh hoạt**:
   - Cho phép sửa Ngày báo cáo, Tháng báo cáo, Hạn chót WO quá hạn, Hạn chót WO tháng.
   - Cho phép sửa trực tiếp số "Thực hiện ngày".
   - Cho phép sửa trực tiếp văn bản trong khung **Preview** trước khi gửi.
   - Lưu cấu hình người nhận và nội dung thông báo mặc định vào `config/config.json`.

4. **Sao chép lên TAMMI cực kỳ tiện lợi**:
   - Nút **[📋 SAO CHÉP BÁO CÁO]** copy trực tiếp plain text Unicode sạch vào Clipboard Windows.
   - Người dùng chỉ cần mở cửa sổ chat TAMMI và bấm `Ctrl + V`.

5. **Xuất file Excel báo cáo chuyên nghiệp**:
   - Tạo file `BaoCao_WO_YYYYMMDD.xlsx`.
   - **Sheet `BaoCao`**: Bố cục đẹp, tiêu đề trang trọng, bảng tổng hợp chỉ số nổi bật, khung thông báo gửi TAMMI.
   - **Sheet `ChiTiet`**: Toàn bộ 14 trung tâm huyện với đầy đủ border, căn chỉnh số liệu, Freeze Panes, AutoFilter.
   - Tùy chọn tự động mở file Excel ngay sau khi xuất.

6. **An toàn dữ liệu tuyệt đối**:
   - File Excel nguồn chỉ được mở ở chế độ READ-ONLY.
   - Tuyệt đối không thay đổi, ghi đè hay làm mất công thức của file nguồn.

---

## 📂 CẤU TRÚC DỰ ÁN

```text
wo_report_tool/
│
├── main.py                     # File khởi chạy ứng dụng
├── requirements.txt            # Danh sách thư viện Python
├── README.md                   # Tài liệu hướng dẫn sử dụng & triển khai
│
├── app/                        # Mã nguồn chính
│   ├── __init__.py             # Định danh package app
│   ├── models.py               # Dataclass ReportData, CenterData, ReportSettings
│   ├── config.py               # Quản lý cấu hình config.json & mapping cột
│   ├── utils.py                # Regex tách mã TT, format ngày tháng, logging
│   ├── excel_reader.py         # Module đọc dữ liệu Excel & worker QThread
│   ├── report_generator.py     # Module sinh text báo cáo chuẩn Word
│   ├── excel_exporter.py       # Module xuất Excel báo cáo (BaoCao & ChiTiet)
│   └── main_window.py          # Giao diện người dùng PySide6
│
├── assets/                     # Tài nguyên đồ họa
│   └── icon.ico                # Icon ứng dụng chất lượng cao
│
├── config/                     # Cấu hình lưu trữ
│   └── config.json             # File cấu hình mặc định (người nhận, deadline, window size)
│
├── samples/                    # File mẫu kiểm thử
│   ├── ĐH WO UT1 (05102026).xlsx
│   └── Mẫu báo cáo NAN_DHKT.docx
│
└── build_scripts/              # Kịch bản đóng gói ứng dụng Windows
    ├── wo_report_tool.spec     # File spec PyInstaller
    ├── build_exe.bat           # File batch 1-click build EXE
    └── setup_installer.iss     # Script Inno Setup 6 tạo bộ cài WOReportTool_Setup.exe
```

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT & CHẠY TỪ SOURCE CODE

### 1. Yêu cầu môi trường:
- Windows 10 hoặc Windows 11 (64-bit).
- Python 3.10, 3.11 hoặc 3.12 (khuyên dùng Python 3.12).

### 2. Cài đặt các thư viện cần thiết:
Mở Terminal / PowerShell tại thư mục `wo_report_tool` và chạy:
```bash
pip install -r requirements.txt
```

### 3. Khởi chạy ứng dụng:
```bash
python main.py
```

---

## 🛠 HƯỚNG DẪN BUILD FILE CHẠY (.EXE) VÀ BỘ CÀI ĐẶT

Người dùng cuối **KHÔNG CẦN CÀI PYTHON**, chỉ cần chạy file ứng dụng đã build.

### Cách 1: Sử dụng file script tự động (Khuyên dùng)
Nhấp đúp chuột vào file:
`wo_report_tool\build_scripts\build_exe.bat`

Script sẽ tự động:
1. Cài đặt các thư viện phụ thuộc.
2. Đóng gói mã nguồn thành thư mục thực thi `dist\WOReportTool\WOReportTool.exe`.
3. Tự động kiểm tra và biên dịch Inno Setup tạo file `dist\WOReportTool_Setup.exe` (nếu máy có cài Inno Setup).

### Cách 2: Chạy lệnh PyInstaller bằng tay
Từ thư mục `wo_report_tool`, chạy:
```bash
pyinstaller --clean -y "build_scripts\wo_report_tool.spec"
```
Kết quả sau khi build nằm tại:
`dist\WOReportTool\WOReportTool.exe`

### Cách 3: Tạo file cài đặt Setup bằng Inno Setup
1. Tải và cài đặt phần mềm miễn phí [Inno Setup 6](https://jrsoftware.org/isdl.php).
2. Mở file `build_scripts\setup_installer.iss` bằng Inno Setup Compiler.
3. Bấm **Compile** (phím `F9` hoặc nút Play xanh).
4. File cài đặt `dist\WOReportTool_Setup.exe` sẽ được tạo ra. Khi gửi file này cho đồng nghiệp, họ chỉ cần bấm Next -> Next -> Install là hoàn tất và có biểu tượng ngoài Desktop.

---

## 📋 MAPPING CẤU TRÚC EXCEL THEO FILE THỰC TẾ

| Chỉ số báo cáo | Tên cột / ô trong Sheet `TH TTH` | Cột Excel | Ghi chú |
| :--- | :--- | :--- | :--- |
| **Thực hiện ngày** | TH Ngày | Cột T (T3) | Lấy tại dòng 3 (Tổng cộng), có thể chỉnh trên GUI |
| **Tổng tồn** | Tồn (nhóm Điều hành UT1) | Cột Q (Q3) | Lấy tại dòng 3, giá trị thực tế = 1008 |
| **Tồn quá hạn** | Tồn QH ngày | Cột R (R3) | Lấy tại dòng 3, giá trị thực tế = 178 |
| **Tồn >30 ngày** | Tồn QH >30 ngày | Cột S (S3) | Lấy tại dòng 3, giá trị thực tế = 1 |
| **Chi tiết >30 ngày** | Cột S của từng dòng huyện | Cột S (S4:S17) | Kết quả thực tế: `(MXN:1)` |
| **Top 5 tồn cao** | Cột Q của từng dòng huyện | Cột Q (Q4:Q17) | Sắp xếp giảm dần: `QLU, DDG, VPU, KLN, YTH` |

---

## 📝 BẢN QUYỀN VÀ HỖ TRỢ
- Dự án phát triển chuyên dụng cho Phòng VHKT - NAN_DHKT.
- Hoạt động 100% Offline, đảm bảo bảo mật và toàn vẹn dữ liệu nội bộ.
