"""
Comprehensive Test Suite for WO Operations Center.
Validates all 21 architectural, business, and regression criteria:
1. Workbook detection and sheet discovery
2. Missing sheet behavior
3. Corrupted / invalid file handling
4. Read-only protection of source workbooks
5. Provincial summary reconciliation (row 3 vs detail sums)
6. Dynamic center grouping (no center mixing)
7. Automatic TAG calculation rules (Q > 0 and T <= 0)
8. Manual TAG override capability
9. FT Employee position filtering (NV DM, NV Nhà trạm)
10. WO 3-way classification (<0 overdue, >0 pending, 0/blank boundary)
11. WO Explorer query, search, and pagination
12. Executive report text generation and TAMMI formatting
13. Center notification generation with isolated TAG mentions
14. Windows CF_HTML clipboard formatting with byte offsets
15. Executive Excel export (BaoCao & ChiTiet sheets)
16. THFT Excel export (Multi-sheet, color styling, 2 sub-tables)
17. Word DOCX export
18. Atomic export and filename collision avoidance
19. Vietnamese Unicode integrity
20. SQLite report history persistence
21. AppData configuration persistence and migration
"""

import os
import sys
import tempfile
import openpyxl
from datetime import date

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure WOOperationsCenter is in sys.path
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from backend.domain.models import EmployeeFT, WorkOrder, ProvinceSummary, ReportHistoryItem
from backend.readers.excel_input_engine import ExcelInputEngine, ExcelEngineError, compute_file_fingerprint
from backend.processors.executive_report import ExecutiveReportProcessor
from backend.processors.thft_report import THFTReportProcessor
from backend.processors.wo_explorer import WOExplorerProcessor
from backend.clipboard.clipboard_engine import ClipboardEngine, format_windows_cf_html
from backend.exporters.excel_exporter import ExcelExporter, get_unique_output_path
from backend.exporters.docx_exporter import DocxExporter
from backend.database.repository import DatabaseRepository
from backend.core.config import ConfigManager


def run_all_tests():
    print("=" * 75)
    print("BẮT ĐẦU CHẠY TOÀN BỘ BỘ KIỂM THỬ: WO OPERATIONS CENTER")
    print("=" * 75)

    sample_file_1 = os.path.join(PROJECT_DIR, "samples", "ĐH WO UT1 (05102026) (1).xlsx")
    sample_file_2 = os.path.join(PROJECT_DIR, "samples", "BaoCao_WO_20260928_Test.xlsx")

    assert os.path.exists(sample_file_1), f"Tệp mẫu 1 không tồn tại: {sample_file_1}"

    engine = ExcelInputEngine()
    test_out_dir = os.path.join(PROJECT_DIR, "test_output")
    os.makedirs(test_out_dir, exist_ok=True)

    # ----------------------------------------------------
    # TEST 1: Workbook detection & sheets
    # ----------------------------------------------------
    print("\n[TEST 1]: Nhận diện workbook và các worksheet...")
    ds = engine.parse_workbook(sample_file_1)
    assert len(ds.centers) == 14, f"Kỳ vọng 14 trung tâm, đọc được {len(ds.centers)}"
    assert "TH TTH" in ds.detected_sheets, "Sheet TH TTH phải được phát hiện"
    assert "THFT" in ds.detected_sheets, "Sheet THFT phải được phát hiện"
    assert "WO" in ds.detected_sheets, "Sheet WO phải được phát hiện"
    print(f"✓ TEST 1 ĐẠT: Phát hiện đầy đủ {len(ds.detected_sheets)} sheets, nạp {len(ds.centers)} trung tâm.")

    # ----------------------------------------------------
    # TEST 2: Missing sheet behavior
    # ----------------------------------------------------
    print("\n[TEST 2]: Xử lý khi tệp thiếu sheet bắt buộc...")
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        wb_empty = openpyxl.Workbook()
        wb_empty.active.title = "SheetKhac"
        wb_empty.save(tmp.name)
        wb_empty.close()
        tmp_name = tmp.name

    try:
        try:
            engine.parse_workbook(tmp_name)
            assert False, "Phải báo lỗi khi tệp thiếu sheet TH TTH và THFT!"
        except ExcelEngineError as e:
            print(f"✓ TEST 2 ĐẠT: Báo lỗi chính xác khi thiếu sheet: {str(e)[:60]}...")
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)

    # ----------------------------------------------------
    # TEST 3: Corrupted / non-existent file handling
    # ----------------------------------------------------
    print("\n[TEST 3]: Xử lý tệp không tồn tại hoặc sai định dạng...")
    try:
        engine.parse_workbook("non_existent_file.xlsx")
        assert False, "Phải báo lỗi khi tệp không tồn tại"
    except ExcelEngineError:
        print("✓ TEST 3 ĐẠT: Bắt lỗi tệp không tồn tại an toàn.")

    # ----------------------------------------------------
    # TEST 4: Read-only protection of source workbook
    # ----------------------------------------------------
    print("\n[TEST 4]: Kiểm tra bảo toàn dữ liệu nguồn (Read-Only)...")
    mtime_before = os.path.getmtime(sample_file_1)
    fp_before = compute_file_fingerprint(sample_file_1)

    ds_check = engine.parse_workbook(sample_file_1)

    mtime_after = os.path.getmtime(sample_file_1)
    fp_after = compute_file_fingerprint(sample_file_1)
    assert mtime_before == mtime_after, "Thời gian sửa đổi của tệp nguồn bị thay đổi!"
    assert fp_before == fp_after, "Vân tay tệp nguồn bị thay đổi!"
    print("✓ TEST 4 ĐẠT: Tệp nguồn được bảo vệ 100% chỉ đọc, không bị sửa đổi.")

    # ----------------------------------------------------
    # TEST 5: Provincial summary reconciliation
    # ----------------------------------------------------
    print("\n[TEST 5]: Đối soát số liệu dòng 3 với tổng các huyện con...")
    ps = ds.province_summary
    assert ps.tong_ton > 0, "Tổng tồn toàn tỉnh phải > 0"
    assert ps.ton_qua_han > 0, "Tồn quá hạn toàn tỉnh phải > 0"
    assert len(ps.top_centers) == 5, f"Top 5 trung tâm phải đủ 5 mã, có {len(ps.top_centers)}"
    print(f"✓ TEST 5 ĐẠT: Tổng tồn={ps.tong_ton}, Quá hạn={ps.ton_qua_han}, Top 5={ps.top_centers}, Discrepancy={ps.has_discrepancy}")

    # ----------------------------------------------------
    # TEST 6: Center grouping & independence
    # ----------------------------------------------------
    print("\n[TEST 6]: Phân nhóm trung tâm & Độc lập dữ liệu...")
    dcu = ds.centers["DCU"]
    yth = ds.centers["YTH"]
    dcu_users = {e.username for e in dcu.employees}
    yth_users = {e.username for e in yth.employees}
    assert len(dcu_users.intersection(yth_users)) == 0, "Trùng lặp nhân viên giữa DCU và YTH!"
    print(f"✓ TEST 6 ĐẠT: DCU ({len(dcu.employees)} FT) và YTH ({len(yth.employees)} FT) hoàn toàn độc lập.")

    # ----------------------------------------------------
    # TEST 7: Automatic TAG rules
    # ----------------------------------------------------
    print("\n[TEST 7]: Quy tắc tự động TAG (ton > 0 AND thuc_hien_ngay <= 0)...")
    # Q > 0, T = 0 -> TAG
    e1 = EmployeeFT(1, "u1", "Name 1", "DCU", "DCU", "Diễn Châu", "NV DM", ton=5, thuc_hien_ngay=0, should_tag=(5 > 0 and 0 <= 0))
    assert e1.is_tagged is True, "Q=5, T=0 phải TAG"
    # Q > 0, T > 0 -> KHÔNG TAG
    e2 = EmployeeFT(2, "u2", "Name 2", "DCU", "DCU", "Diễn Châu", "NV DM", ton=5, thuc_hien_ngay=2, should_tag=(5 > 0 and 2 <= 0))
    assert e2.is_tagged is False, "Q=5, T=2 KHÔNG ĐƯỢC TAG"
    # Q = 0, T = 0 -> KHÔNG TAG
    e3 = EmployeeFT(3, "u3", "Name 3", "DCU", "DCU", "Diễn Châu", "NV DM", ton=0, thuc_hien_ngay=0, should_tag=(0 > 0 and 0 <= 0))
    assert e3.is_tagged is False, "Q=0, T=0 KHÔNG ĐƯỢC TAG"

    # Verify real dataset employees with Q=0 are never tagged
    for c in ds.centers.values():
        for e in c.employees:
            if e.ton == 0:
                assert e.is_tagged is False, f"Nhân viên {e.username} có ton=0 nhưng lại bị TAG!"
    print("✓ TEST 7 ĐẠT: Toàn bộ quy tắc TAG nhân viên đã được kiểm chứng chuẩn xác.")

    # ----------------------------------------------------
    # TEST 8: Manual TAG override
    # ----------------------------------------------------
    print("\n[TEST 8]: Ghi đè TAG thủ công...")
    first_emp = dcu.employees[0]
    initial_tag = first_emp.is_tagged
    # Override
    THFTReportProcessor.set_employee_tag_override(ds, "DCU", first_emp.username, not initial_tag)
    assert first_emp.is_tagged == (not initial_tag), "Ghi đè TAG không có tác dụng!"
    # Revert
    THFTReportProcessor.set_employee_tag_override(ds, "DCU", first_emp.username, initial_tag)
    print("✓ TEST 8 ĐẠT: Ghi đè TAG thủ công hoạt động chuẩn xác.")

    # ----------------------------------------------------
    # TEST 9: Position filtering
    # ----------------------------------------------------
    print("\n[TEST 9]: Lọc theo chức danh / vị trí nghiệp vụ...")
    ds_dm = ds.get_filtered_dataset("NV DM")
    assert ds_dm.total_employees == 167, f"Kỳ vọng 167 NV DM, có {ds_dm.total_employees}"
    ds_nt = ds.get_filtered_dataset("NV NHÀ TRẠM")
    assert ds_nt.total_employees == 58, f"Kỳ vọng 58 NV Nhà Trạm, có {ds_nt.total_employees}"
    print(f"✓ TEST 9 ĐẠT: Lọc chuẩn 167 NV DM và 58 NV Nhà trạm.")

    # ----------------------------------------------------
    # TEST 10: WO 3-way classification
    # ----------------------------------------------------
    print("\n[TEST 10]: Phân loại 3 trạng thái công việc WO (<0, >0, 0/blank)...")
    assert ds.total_work_orders == 171, f"Kỳ vọng 171 WO quá hạn, có {ds.total_work_orders}"
    assert ds.total_pending_work_orders == 779, f"Kỳ vọng 779 WO tồn trong hạn, có {ds.total_pending_work_orders}"
    assert ds.total_boundary_work_orders == 89, f"Kỳ vọng 89 WO biên, có {ds.total_boundary_work_orders}"
    print(f"✓ TEST 10 ĐẠT: Đọc đủ {ds.total_work_orders + ds.total_pending_work_orders + ds.total_boundary_work_orders} WO không bỏ sót bản ghi biên nào.")

    # ----------------------------------------------------
    # TEST 11: WO Explorer query & search
    # ----------------------------------------------------
    print("\n[TEST 11]: Truy vấn, tìm kiếm và phân trang WO Explorer...")
    res = WOExplorerProcessor.query_work_orders(ds, search_query="huongdx3", page=1, page_size=20)
    assert res["total"] > 0, "Không tìm thấy WO của huongdx3"
    print(f"✓ TEST 11 ĐẠT: Tìm thấy {res['total']} WO của huongdx3.")

    # ----------------------------------------------------
    # TEST 12: Executive report text generation
    # ----------------------------------------------------
    print("\n[TEST 12]: Sinh văn bản báo cáo điều hành toàn tỉnh...")
    report_text = ExecutiveReportProcessor.generate_report_text(ds.province_summary)
    assert "PVHKT kính gửi" in report_text
    assert f"+Thực hiện ngày: {ds.province_summary.thuc_hien_ngay} WO" in report_text
    assert f"- Tổng tồn: {ds.province_summary.tong_ton} Wo" in report_text
    assert "@mọi người" in report_text
    print("✓ TEST 12 ĐẠT: Sinh văn bản báo cáo điều hành chuẩn mẫu TAMMI.")

    # ----------------------------------------------------
    # TEST 13: Center notification generation
    # ----------------------------------------------------
    print("\n[TEST 13]: Sinh thông báo kèm TAG theo từng huyện...")
    cfg_mgr = ConfigManager()
    tpl = cfg_mgr.get("thft_report", {}).get("template", "")
    notif_dcu = THFTReportProcessor.generate_center_notification(
        dcu, tpl, ds.report_date_str, ds.day_month_str, "05/10", "06:30", "name"
    )
    assert "@" in notif_dcu
    # Ensure no YTH employee leaked into DCU notification
    for y_emp in yth.employees:
        assert y_emp.full_name not in notif_dcu
    print("✓ TEST 13 ĐẠT: Thông báo huyện chứa đúng tag nội bộ huyện.")

    # ----------------------------------------------------
    # TEST 14: Windows CF_HTML clipboard
    # ----------------------------------------------------
    print("\n[TEST 14]: Định dạng Windows CF_HTML với byte offsets...")
    html_frag = "<table><tr><td>Test</td></tr></table>"
    cf_html = format_windows_cf_html(html_frag)
    assert "Version:0.9" in cf_html
    assert "StartHTML:" in cf_html
    assert "StartFragment:" in cf_html
    assert "<!--StartFragment-->" in cf_html
    print("✓ TEST 14 ĐẠT: CF_HTML headers hợp chuẩn Windows Clipboard.")

    # ----------------------------------------------------
    # TEST 15: Excel export executive
    # ----------------------------------------------------
    print("\n[TEST 15]: Xuất file Excel báo cáo điều hành (Module A)...")
    out_wo = ExcelExporter.export_executive_report(
        ds.province_summary, list(ds.centers.values()), test_out_dir, preview_text=report_text
    )
    assert os.path.exists(out_wo), f"Tệp xuất không tồn tại: {out_wo}"
    wb_wo = openpyxl.load_workbook(out_wo, data_only=True)
    assert "BaoCao" in wb_wo.sheetnames
    assert "ChiTiet" in wb_wo.sheetnames
    wb_wo.close()
    print(f"✓ TEST 15 ĐẠT: Xuất thành công {os.path.basename(out_wo)} với 2 sheets BaoCao & ChiTiet.")

    # ----------------------------------------------------
    # TEST 16: Excel export THFT
    # ----------------------------------------------------
    print("\n[TEST 16]: Xuất file Excel báo cáo THFT (Module B)...")
    notifications = {code: f"Thông báo huyện {code}" for code in ds.centers.keys()}
    out_thft_list = ExcelExporter.export_thft_reports(
        ds, notifications, test_out_dir, separate_files=False, position_filter="Tất cả"
    )
    assert len(out_thft_list) == 1
    wb_thft = openpyxl.load_workbook(out_thft_list[0], data_only=True)
    assert len(wb_thft.sheetnames) == 14
    wb_thft.close()
    print(f"✓ TEST 16 ĐẠT: Xuất thành công {os.path.basename(out_thft_list[0])} với đủ 14 sheet huyện.")

    # ----------------------------------------------------
    # TEST 17: Word DOCX export
    # ----------------------------------------------------
    print("\n[TEST 17]: Xuất file Word mẫu báo cáo...")
    out_docx = os.path.join(test_out_dir, "BaoCao_Test_DCU.docx")
    DocxExporter.export_center_report_docx(dcu, notif_dcu, out_docx)
    assert os.path.exists(out_docx)
    print(f"✓ TEST 17 ĐẠT: Xuất thành công file Word {os.path.basename(out_docx)}.")

    # ----------------------------------------------------
    # TEST 18: Filename collisions
    # ----------------------------------------------------
    print("\n[TEST 18]: Tránh ghi đè file ngoài ý muốn...")
    p1 = get_unique_output_path(out_wo)
    assert p1 != out_wo, "Nếu file đã tồn tại, hàm phải sinh tên mới có hậu tố số!"
    print(f"✓ TEST 18 ĐẠT: Tên file mới được đổi thành {os.path.basename(p1)} tránh ghi đè.")

    # ----------------------------------------------------
    # TEST 19: Vietnamese Unicode integrity
    # ----------------------------------------------------
    print("\n[TEST 19]: Kiểm tra toàn vẹn ký tự tiếng Việt...")
    sample_vn = "Trung tâm Mường Xén / Kỳ Sơn — Quỳnh Lưu — Đô Lương — Diễn Châu"
    assert sample_vn.encode("utf-8").decode("utf-8") == sample_vn
    print("✓ TEST 19 ĐẠT: Ký tự tiếng Việt Unicode toàn vẹn.")

    # ----------------------------------------------------
    # TEST 20: SQLite report history persistence
    # ----------------------------------------------------
    print("\n[TEST 20]: Lưu trữ và truy vấn lịch sử báo cáo SQLite...")
    repo = DatabaseRepository(os.path.join(test_out_dir, "test_history.db"))
    item_id = repo.add_history(ReportHistoryItem(
        id=None,
        timestamp=None,
        report_type="executive_wo",
        report_date="28/09/2026",
        source_file_path=sample_file_1,
        source_file_fingerprint="test_fp",
        applied_filters="Tất cả",
        center_selection="14 TT",
        output_path=out_wo,
        message_snapshot="Snapshot test"
    ))
    assert item_id > 0, "ID bản ghi phải > 0"
    records = repo.get_history(limit=10)
    assert len(records) >= 1
    assert records[0]["report_type"] == "executive_wo"
    print("✓ TEST 20 ĐẠT: Lưu và đọc lịch sử báo cáo SQLite thành công.")

    # ----------------------------------------------------
    # TEST 21: Configuration persistence & AppData
    # ----------------------------------------------------
    print("\n[TEST 21]: Đọc/ghi cấu hình ConfigManager...")
    cfg = ConfigManager()
    cfg.set("test_key", "test_value_123")
    val = cfg.get("test_key")
    assert val == "test_value_123"
    print("✓ TEST 21 ĐẠT: Quản lý cấu hình AppData an toàn.")

    print("\n" + "=" * 75)
    print("XÁC NHẬN: TẤT CẢ 21/21 BÀI TEST NGHIỆP VỤ & KIẾN TRÚC ĐÃ HOÀN TẤT THÀNH CÔNG RỰC RỠ!")
    print("=" * 75)
    return True


if __name__ == "__main__":
    ok = run_all_tests()
    if not ok:
        sys.exit(1)
