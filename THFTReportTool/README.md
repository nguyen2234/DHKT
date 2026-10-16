# CÔNG CỤ TẠO BÁO CÁO THFT

Ứng dụng Windows Desktop chuyên nghiệp phát triển bằng **Python 3.12** và **PySide6**, phục vụ tự động hóa quy trình tổng hợp báo cáo điều hành WO UT1, tính toán số liệu và gắn thẻ (TAG) nhân viên kỹ thuật FT theo từng Trung tâm Huyện.

---

## 🌟 TÍNH NĂNG NỔI BẬT

1. **Phân nhóm tự động theo Trung tâm Huyện**:
   - Tự động quét và gom nhóm toàn bộ nhân viên theo từng Trung tâm Huyện (VPU, KLN, NLC, DCU, YTH, QLU, THU, QHP, QPG, TKY, DDG, VTG, TDG, MXN...).
   - Không hard-code danh sách huyện.
2. **Lọc theo vị trí nghiệp vụ (Cột D)**:
   - Thêm bộ lọc linh hoạt trực tiếp trên giao diện:
     - **Tất cả vị trí** (229 FT)
     - **Nhân viên DM** (167 FT - `NV DM`)
     - **Nhân viên nhà trạm** (58 FT - `NV NHÀ TRẠM`)
   - Toàn bộ danh sách huyện, huy hiệu số lượng, xem trước báo cáo, danh sách TAG, bảng kiểm tra và file Excel xuất ra sẽ tự động lọc chính xác theo vị trí đã chọn.
   - Hậu tố tên file tự động phân biệt rõ ràng: `BaoCao_THFT_YYYYMMDD_NVDM.xlsx` hoặc `BaoCao_THFT_YYYYMMDD_NVNhaTram.xlsx`.
3. **Logic TAG nhân viên chuẩn xác tuyệt đối**:
   - **ĐIỀU KIỆN TAG**: Cột Q (TỒN) > 0 VÀ Cột T (THỰC HIỆN NGÀY) ≤ 0 (rỗng hoặc = 0).
   - **KHÔNG TAG**: Khi Q = 0 hoặc khi nhân viên đã có tiến độ ngày (T > 0).
   - **ĐỘC LẬP TỪNG HUYỆN**: Báo cáo huyện nào chỉ gắn tag nhân viên thuộc huyện đó.
   - Bảng kiểm tra tương tác: Cho phép người dùng bật/tắt checkbox tag thủ công trước khi xuất.
3. **Mẫu thông báo linh hoạt & Xem trước trực tiếp**:
   - Tự động điền ngày báo cáo, hạn hoàn thành, giờ họp, danh sách tag.
   - Người dùng được phép chỉnh sửa trực tiếp nội dung thông báo ngay trên giao diện.
   - Nhiều định dạng tag: `@Họ và tên`, `@HỌ VÀ TÊN`, `@Username`, `@FT Username`.
4. **Copy trực tiếp lên TAMMY & Excel**:
   - Nút **[📋 COPY BÁO CÁO HUYỆN]**: Tạo đồng thời định dạng **HTML Table** (có màu sắc, viền, font chữ mô phỏng Word mẫu) và **Plain Text** cho Clipboard Windows. Khi nhấn `Ctrl+V` trên hệ thống TAMMY, web portal, Word hoặc Teams sẽ hiển thị bảng biểu cực kỳ đẹp mắt và dễ đọc.
   - Nút **[💬 COPY THÔNG BÁO + TAG]**: Hỗ trợ copy nhanh phần văn bản thông báo và danh sách @tag.
   - Nút **[⚠️ COPY WO QUÁ HẠN]**: Hỗ trợ copy toàn bộ danh sách WO quá hạn của huyện đang chọn lên Clipboard (hỗ trợ cả bảng HTML và TSV để paste trực tiếp vào Excel chuẩn cột).
   - Nút **[⏳ COPY WO CHƯA QUÁ HẠN]**: Hỗ trợ copy toàn bộ danh sách WO tồn chưa quá hạn (cột L > 0) của huyện đang chọn lên Clipboard.
5. **Xuất file Excel chuyên nghiệp (Mỗi huyện 1 Sheet & Bảng WO Quá Hạn + Bảng WO Tồn Chưa Quá Hạn Phía Dưới)**:
   - File kết quả: `BaoCao_THFT_YYYYMMDD[_NVDM].xlsx`.
   - Mỗi huyện là một worksheet riêng biệt.
   - Bố cục bám sát file mẫu Word (`mẫu báo cáo FT.docx`):
     - Phần trên: Card thông báo và danh sách TAG.
     - Phần giữa: Bảng nhân viên đầy đủ 20 cột (A -> T), phối màu chuẩn theo từng nhóm nghiệp vụ:
       - Cột A-D: Xanh lục lá nhạt (`#92D050`)
       - Cột E-G (ICMS Bảo dưỡng nhà trạm): Xanh ô-liu (`#EBF1DE`)
       - Cột H-J (ICMS Bảo dưỡng THC): Màu cam đào (`#FDE9D9`)
       - Cột K-M (ICMS Tuần tra tuyến cáp): Xanh lam ngọc (`#92CDDC`)
       - Cột N-P (Báo hỏng hạ tầng mạng lưới): Xanh dương đậm chữ trắng (`#0070C0`)
       - Cột Q-S (Tổng Tồn, Quá hạn, QH 30N): Xanh lục lá (`#92D050`)
       - Cột T (Thực hiện ngày): Đỏ tươi chữ trắng (`#FF0000`)
     - Hàng tổng cộng (Subtotal) ở cuối bảng FT mỗi huyện.
     - **BẢNG WO QUÁ HẠN PHÍA DƯỚI**: Tự động trích xuất các công việc từ sheet `WO` có **Cột L (Ngày quá hạn) có giá trị âm (< 0)**, sắp xếp theo từng huyện và hiển thị ngay phía dưới bảng FT với đầy đủ 15 cột thông tin (tông màu Xanh dương đậm Navy `#1F4E78`), số ngày quá hạn bôi đỏ nổi bật, kèm hàng tổng cộng.
     - **BẢNG WO TỒN CHƯA QUÁ HẠN PHÍA DƯỚI**: Tự động trích xuất các công việc từ sheet `WO` có **Cột L (Ngày quá hạn) có giá trị dương (> 0)**, hiển thị ngay phía dưới bảng WO quá hạn với giao diện phối màu phân biệt thanh lịch (tông màu Xanh lá / Rừng ngọc bích `#135E48` / `#1E8449` / `#D5F5E3`), số ngày còn lại bôi xanh nổi bật, kèm hàng tổng cộng. Người dùng có thể theo dõi và copy danh sách các công việc còn trong hạn thực hiện.
     - Thiết lập in sẵn sàng: Khổ giấy A4, hướng ngang (Landscape), Fit to 1 Page Width, Narrow Margins.
6. **Hiệu năng & An toàn**:
   - Đọc siêu tốc bằng openpyxl stream read-only (chỉ mất ~2 giây cho file Excel 30MB).
   - Đa luồng (QThread Worker) đảm bảo giao diện luôn mượt mà, có thanh tiến trình (progress bar).
   - **Tuyệt đối KHÔNG sửa đổi, không ghi đè file dữ liệu nguồn**.
   - Hoạt động 100% offline, không gửi dữ liệu ra bên ngoài.

---

## 📊 BẢNG MAPPING CỘT DỮ LIỆU TỪ EXCEL

| Cột | Tên Cột (Hàng 1 & 2) | Ý Nghĩa Nghiệp Vụ | Ghi Chú |
|:---:|:---|:---|:---|
| **A** | FT | Tài khoản / Username nhân viên FT | Ví dụ: `huongdx3`, `longht1` |
| **B** | Tên FT | Họ và tên nhân viên FT | Ví dụ: `Đinh Xuân Hương` |
| **C** | TTH | Trung tâm Huyện | Tự động tách Mã và Tên Huyện |
| **D** | Vị trí | Vị trí công việc | Ví dụ: `NV DM`, `NV NHÀ TRẠM` |
| **E** | ICMS_Bảo dưỡng nhà trạm - Tồn | Số lượng tồn BD nhà trạm | Số nguyên (ẩn nếu = 0) |
| **F** | ICMS_Bảo dưỡng nhà trạm - Quá hạn | Quá hạn BD nhà trạm | Số nguyên |
| **G** | ICMS_Bảo dưỡng nhà trạm - Quá hạn 30N | Quá hạn >30 ngày BD nhà trạm | Số nguyên |
| **H** | ICMS_Bảo dưỡng THC - Tồn | Tồn BD thuê bao THC | Số nguyên |
| **I** | ICMS_Bảo dưỡng THC - Quá hạn | Quá hạn BD THC | Số nguyên |
| **J** | ICMS_Bảo dưỡng THC - Quá hạn 30N | Quá hạn >30 ngày BD THC | Số nguyên |
| **K** | ICMS_Tuần tra tuyến cáp - Tồn | Tồn tuần tra tuyến cáp | Số nguyên |
| **L** | ICMS_Tuần tra tuyến cáp - Quá hạn | Quá hạn tuần tra tuyến cáp | Số nguyên |
| **M** | ICMS_Tuần tra tuyến cáp - Quá hạn 30N | Quá hạn >30 ngày tuyến cáp | Số nguyên |
| **N** | Báo hỏng hạ tầng mạng lưới - Tồn | Tồn báo hỏng mạng lưới | Số nguyên |
| **O** | Báo hỏng hạ tầng mạng lưới - Quá hạn | Quá hạn báo hỏng | Số nguyên |
| **P** | Báo hỏng hạ tầng mạng lưới - Quá hạn 30N | Quá hạn >30 ngày báo hỏng | Số nguyên |
| **Q** | **Tổng - Tồn** | **TỔNG SỐ LƯỢNG WO TỒN** | **CỘT ĐIỀU KIỆN 1 ĐỂ TAG (Q > 0)** |
| **R** | Tổng - Quá hạn | Tổng số lượng quá hạn | Bôi đậm trong báo cáo |
| **S** | Tổng - Quá hạn 30N | Tổng số quá hạn > 30 ngày | |
| **T** | **Thực hiện ngày** | **TIẾN ĐỘ THỰC HIỆN TRONG NGÀY** | **CỘT ĐIỀU KIỆN 2: T ≤ 0 HOẶC RỖNG => TAG** |

---

## 📊 BẢNG MAPPING CỘT TỪ SHEET 'WO' (DANH SÁCH CHI TIẾT WO)

| Cột | Tên Cột | Ý Nghĩa Nghiệp Vụ | Quy Tắc Xử Lý |
|:---:|:---|:---|:---|
| **A** | STT | Số thứ tự công việc | Đánh số tự động tăng dần |
| **B** | Mã công việc | Mã định danh WO | Ví dụ: `WO_ICMS_20260827_...` |
| **C** | Loại công việc | Phân loại nghiệp vụ | Ví dụ: `ICMS_Bảo dưỡng nhà trạm`, `Bảo dưỡng THC` |
| **D** | Nội dung công việc | Mô tả chi tiết hạng mục | Đầy đủ nội dung trạm, định kỳ |
| **E** | Thời điểm yêu cầu kết thúc | Deadline kết thúc WO | Định dạng `dd/MM/yyyy HH:mm:ss` |
| **F** | Trạng thái | Tình trạng WO | Đã giao FT, FT Đang thực hiện, Đóng... |
| **G** | Nhân viên thực hiện | Tài khoản nhân sự phụ trách | Sắp xếp theo nhân viên trong từng huyện |
| **H** | Mã trạm | Mã trạm thực hiện | Ví dụ: `NAN3978`, `NAN1716` |
| **I** | FT comment | Ghi chú của nhân viên | Giữ nguyên dữ liệu gốc |
| **J** | FT mobile | Số điện thoại liên hệ | Giữ nguyên dữ liệu gốc |
| **K** | Ngày hoàn thành | Thời điểm đóng/hoàn thành | Giữ nguyên dữ liệu gốc |
| **L** | **Ngày quá hạn** | **SỐ NGÀY QUÁ HẠN / CÒN LẠI** | **< 0: WO QUÁ HẠN (Bảng Navy Blue)<br>> 0: WO TỒN CHƯA QUÁ HẠN (Bảng Forest Green)** |
| **M** | **TTH** | **TRUNG TÂM HUYỆN** | **Tự động tách mã huyện để gom nhóm vào đúng Sheet** |
| **N** | BKK | Bất khả kháng | Giữ nguyên dữ liệu gốc |
| **O** | Lý do BKK | Chi tiết lý do bất khả kháng | Giữ nguyên dữ liệu gốc |

## 🎯 QUY TẮC TAG NHÂN VIÊN

```python
if ton > 0 and thuc_hien_ngay <= 0:
    can_tag = True
else:
    can_tag = False
```

- **Ví dụ 1**: Nguyễn Văn A có Q = 5, T = 0  -> **TAG**
- **Ví dụ 2**: Nguyễn Văn B có Q = 3, T = rỗng -> **TAG**
- **Ví dụ 3**: Nguyễn Văn C có Q = 4, T = 2  -> **KHÔNG TAG** (đã có tiến độ trong ngày)
- **Ví dụ 4**: Nguyễn Văn D có Q = 0, T = 0  -> **KHÔNG TAG** (không có WO tồn)

---

## 📁 CẤU TRÚC DỰ ÁN

```
THFTReportTool/
│
├── main.py                     # File khởi động chính của ứng dụng
├── requirements.txt           # Danh sách thư viện Python cần thiết
├── README.md                  # Tài liệu hướng dẫn sử dụng và phát triển
├── build.bat                  # Script đóng gói tự động EXE và Setup
├── THFTReportTool.spec        # Cấu hình đóng gói PyInstaller
│
├── app/
│   ├── __init__.py
│   ├── main_window.py         # Giao diện người dùng PySide6 hiện đại
│   ├── excel_reader.py        # Module đọc, xác thực và phân tích file Excel
│   ├── word_template_reader.py# Module phân tích file mẫu Word docx
│   ├── report_processor.py    # Xử lý nghiệp vụ, template thông báo & tag
│   ├── report_exporter.py     # Xuất workbook Excel nhiều sheet, chuẩn in
│   ├── clipboard_manager.py   # Quản lý clipboard HTML & Text cho TAMMY
│   ├── models.py              # Data models (EmployeeFT, CenterReport, Dataset)
│   ├── config.py              # Quản lý đọc/ghi cấu hình config.json
│   └── utils.py               # Các hàm tiện ích xử lý chuỗi, số, ngày tháng
│
├── config/
│   └── config.json            # File cấu hình mapping cột và template mặc định
│
├── assets/
│   └── icon.ico               # Icon ứng dụng chất lượng cao
│
├── samples/                   # File dữ liệu và file mẫu Word thử nghiệm
│   ├── ĐH WO UT1 (05102026) (1).xlsx
│   └── mẫu báo cáo FT.docx
│
├── installer/
│   └── THFTReportTool.iss     # Kịch bản tạo bộ cài đặt Inno Setup
│
└── test_all.py                # Bộ test tự động kiểm thử toàn diện 16/16 yêu cầu nghiệp vụ
```

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT & CHẠY

### 1. Chạy từ mã nguồn Python

Yêu cầu máy tính đã cài **Python 3.12**:

```bash
# Cài đặt các thư viện cần thiết
pip install -r requirements.txt

# Khởi chạy chương trình
python main.py
```

### 2. Chạy thử nghiệm bộ test tự động

```bash
python test_all.py
```

---

## 📦 ĐÓNG GÓI THÀNH FILE .EXE VÀ FILE CÀI ĐẶT .SETUP

Chạy file batch:

```bash
build.bat
```

Sau khi hoàn tất:
- Bản chạy trực tiếp không cần cài Python: `dist\THFTReportTool\THFTReportTool.exe`
- File cài đặt chuẩn Windows Setup: `dist_installer\THFTReportTool_Setup.exe`
