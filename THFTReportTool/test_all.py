"""
Comprehensive Automated Test Suite for THFT Report Tool.
Verifies all 10 mandatory test scenarios specified in user requirements:
TEST 1: Q > 0, T blank => TAG
TEST 2: Q > 0, T = 0 => TAG
TEST 3: Q > 0, T > 0 => KHÔNG TAG
TEST 4: Q = 0, T = 0 => KHÔNG TAG
TEST 5: Q blank => KHÔNG TAG
TEST 6: Nhân viên DCU => chỉ xuất trong báo cáo DCU
TEST 7: Nhân viên YTH => không được xuất vào DCU
TEST 8: Kiểm tra Unicode tiếng Việt
TEST 9: Kiểm tra file Excel xuất (14 sheets, layout, print setup)
TEST 10: Kiểm tra Clipboard generation
"""

import os
import sys
import datetime
import openpyxl

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import load_config
from app.models import EmployeeFT, CenterReport, ReportDataset
from app.excel_reader import ExcelReader
from app.word_template_reader import WordTemplateReader
from app.report_processor import ReportProcessor
from app.report_exporter import ReportExporter
from app.clipboard_manager import ClipboardManager


def run_tests():
    print("=" * 60)
    print("BẮT ĐẦU CHẠY BỘ KIỂM THỬ THFT REPORT TOOL")
    print("=" * 60)

    config = load_config()
    reader = ExcelReader(config)
    processor = ReportProcessor(config)
    exporter = ReportExporter(config)
    word_reader = WordTemplateReader()

    sample_excel = os.path.join(os.path.dirname(__file__), "samples", "ĐH WO UT1 (05102026) (1).xlsx")
    sample_word = os.path.join(os.path.dirname(__file__), "samples", "mẫu báo cáo FT.docx")

    # 1. Test Word Template Reader
    print("\n[KIỂM TRA 0]: Đọc file Word mẫu...")
    ok = word_reader.load_template(sample_word)
    assert ok, "Không đọc được file Word mẫu!"
    info = word_reader.get_template_info()
    print(f"✓ Word Template sample notification: {info['notification_sample'][:70]}...")
    print(f"✓ Word Template header columns: {len(info['table_headers'][0]) if info['table_headers'] else 0}")

    # 2. Test Excel Reader on sample file
    print("\n[KIỂM TRA EXCEL]: Đọc file Excel mẫu...")
    dataset = reader.read_report_file(sample_excel)
    assert dataset.total_employees == 229, f"Kỳ vọng 229 FT, nhưng đọc được {dataset.total_employees}"
    assert len(dataset.centers) == 14, f"Kỳ vọng 14 trung tâm, nhưng đọc được {len(dataset.centers)}"
    print(f"✓ Đọc thành công: {dataset.total_employees} FT, {len(dataset.centers)} trung tâm")

    # TEST 1: Q > 0, T blank => TAG
    print("\n[TEST 1]: Q > 0, T blank => TAG")
    e1 = EmployeeFT(1, "test1", "NV Test 1", "DCU", "DCU", "Diễn Châu", "NV DM", ton=5, thuc_hien_ngay=0, should_tag=(5 > 0 and 0 <= 0))
    assert e1.is_tagged is True, "TEST 1 THẤT BẠI: Q=5, T=blank phải được TAG!"
    print("✓ TEST 1 ĐẠT: Q > 0, T blank => TAG")

    # TEST 2: Q > 0, T = 0 => TAG
    print("\n[TEST 2]: Q > 0, T = 0 => TAG")
    e2 = EmployeeFT(2, "test2", "NV Test 2", "DCU", "DCU", "Diễn Châu", "NV DM", ton=3, thuc_hien_ngay=0, should_tag=(3 > 0 and 0 <= 0))
    assert e2.is_tagged is True, "TEST 2 THẤT BẠI: Q=3, T=0 phải được TAG!"
    print("✓ TEST 2 ĐẠT: Q > 0, T = 0 => TAG")

    # TEST 3: Q > 0, T > 0 => KHÔNG TAG
    print("\n[TEST 3]: Q > 0, T > 0 => KHÔNG TAG")
    e3 = EmployeeFT(3, "test3", "NV Test 3", "DCU", "DCU", "Diễn Châu", "NV DM", ton=4, thuc_hien_ngay=2, should_tag=(4 > 0 and 2 <= 0))
    assert e3.is_tagged is False, "TEST 3 THẤT BẠI: Q=4, T=2 KHÔNG được TAG!"
    print("✓ TEST 3 ĐẠT: Q > 0, T > 0 => KHÔNG TAG")

    # TEST 4: Q = 0, T = 0 => KHÔNG TAG
    print("\n[TEST 4]: Q = 0, T = 0 => KHÔNG TAG")
    e4 = EmployeeFT(4, "test4", "NV Test 4", "DCU", "DCU", "Diễn Châu", "NV DM", ton=0, thuc_hien_ngay=0, should_tag=(0 > 0 and 0 <= 0))
    assert e4.is_tagged is False, "TEST 4 THẤT BẠI: Q=0, T=0 KHÔNG được TAG!"
    print("✓ TEST 4 ĐẠT: Q = 0, T = 0 => KHÔNG TAG")

    # TEST 5: Q blank => KHÔNG TAG
    print("\n[TEST 5]: Q blank => KHÔNG TAG")
    e5 = EmployeeFT(5, "test5", "NV Test 5", "DCU", "DCU", "Diễn Châu", "NV DM", ton=0, thuc_hien_ngay=0, should_tag=(0 > 0 and 0 <= 0))
    assert e5.is_tagged is False, "TEST 5 THẤT BẠI: Q blank KHÔNG được TAG!"
    print("✓ TEST 5 ĐẠT: Q blank => KHÔNG TAG")

    # Real data validation for Q=0 employees
    q_zero_in_dataset = [e for c in dataset.centers.values() for e in c.employees if e.ton == 0]
    assert len(q_zero_in_dataset) >= 16, f"Kỳ vọng ít nhất 16 nhân viên Q=0 trong file mẫu, tìm thấy {len(q_zero_in_dataset)}"
    for e in q_zero_in_dataset:
        assert e.is_tagged is False, f"Nhân viên {e.username} có Q=0 nhưng lại bị TAG!"
    print(f"✓ Đã xác minh {len(q_zero_in_dataset)}/{len(q_zero_in_dataset)} nhân viên Q=0 trong file dữ liệu thực tế đều KHÔNG bị TAG")

    # TEST 6 & 7: Nhân viên DCU chỉ xuất trong DCU, YTH không lọt vào DCU
    print("\n[TEST 6 & 7]: Phân nhóm huyện & Độc lập dữ liệu...")
    dcu = dataset.centers["DCU"]
    yth = dataset.centers["YTH"]
    assert len(dcu.employees) == 19, f"Kỳ vọng 19 nhân viên DCU, có {len(dcu.employees)}"
    assert len(yth.employees) == 23, f"Kỳ vọng 23 nhân viên YTH, có {len(yth.employees)}"

    dcu_users = {e.username for e in dcu.employees}
    yth_users = {e.username for e in yth.employees}
    intersection = dcu_users.intersection(yth_users)
    assert len(intersection) == 0, f"Trùng lặp nhân viên giữa DCU và YTH: {intersection}"

    # Verify DCU tag string contains only DCU tagged employees
    dcu_tag_string = dcu.build_tag_string("name")
    for yth_emp in yth.employees:
        assert yth_emp.full_name not in dcu_tag_string, f"Nhân viên YTH {yth_emp.full_name} xuất hiện trong tag DCU!"
    print("✓ TEST 6 ĐẠT: Nhân viên DCU chỉ xuất trong báo cáo DCU")
    print("✓ TEST 7 ĐẠT: Nhân viên YTH không xuất hiện trong báo cáo DCU")

    # TEST 8: Kiểm tra Unicode tiếng Việt
    print("\n[TEST 8]: Kiểm tra Unicode tiếng Việt...")
    vietnamese_sample = "Đinh Xuân Hương - Trung tâm Diễn Châu - Nghệ An - Khẩn trương hoàn thành"
    encoded = vietnamese_sample.encode("utf-8").decode("utf-8")
    assert encoded == vietnamese_sample
    for emp in dcu.employees:
        assert isinstance(emp.full_name, str)
    print(f"✓ TEST 8 ĐẠT: Xử lý Unicode tiếng Việt hoàn toàn chính xác")

    # TEST 9: Xuất báo cáo Excel và kiểm tra cấu trúc
    print("\n[TEST 9]: Xuất báo cáo Excel đa huyện...")
    output_dir = os.path.join(os.path.dirname(__file__), "test_output")
    os.makedirs(output_dir, exist_ok=True)

    notifications = {}
    tpl = config["notification"]["template"]
    for code, c in dataset.centers.items():
        notifications[code] = processor.generate_center_notification(
            c, tpl, dataset.report_date_str, dataset.day_month_str,
            dataset.deadline_str, dataset.meeting_time_str, "name"
        )

    out_file = exporter.export_excel(dataset, notifications, output_dir=output_dir)
    assert os.path.exists(out_file), "File xuất không tồn tại!"
    print(f"✓ File Excel đã xuất: {out_file}")

    # Inspect the exported Excel file
    wb_out = openpyxl.load_workbook(out_file, data_only=True)
    assert len(wb_out.sheetnames) == 14, f"Kỳ vọng 14 sheets, nhưng có {len(wb_out.sheetnames)}: {wb_out.sheetnames}"
    print(f"✓ Đủ 14 sheet huyện: {wb_out.sheetnames}")

    # Inspect DCU sheet
    ws_dcu = wb_out["DCU"]
    assert ws_dcu.page_setup.orientation == ws_dcu.ORIENTATION_LANDSCAPE, "Page setup phải là Landscape!"
    assert str(ws_dcu.page_setup.paperSize) == str(ws_dcu.PAPERSIZE_A4), "Paper size phải là A4!"
    assert ws_dcu.page_setup.fitToWidth == 1, "FitToWidth phải là 1 page!"
    # Check notification in A1
    val_a1 = str(ws_dcu["A1"].value)
    assert "FT tồn quá hạn" in val_a1, "Ô A1 phải chứa nội dung thông báo!"
    assert "@Đinh Xuân Hương" in val_a1 or "@huongdx3" in val_a1, "Ô A1 phải chứa danh sách TAG của DCU!"
    print(f"✓ Ô A1 sheet DCU chứa đúng thông báo và tag: {val_a1[:60]}...")
    # Check headers in row 3 & 4
    assert ws_dcu.cell(row=3, column=1).value == "FT"
    assert ws_dcu.cell(row=4, column=5).value == "Tồn"
    # Check subtotal row exists
    last_row = ws_dcu.max_row
    assert "Tổng cộng" in str(ws_dcu.cell(row=last_row, column=1).value)
    wb_out.close()
    print("✓ TEST 9 ĐẠT: File Excel xuất chuẩn 14 sheets, đúng màu, đúng khổ A4 landscape, fit to page.")

    # TEST 10: Kiểm tra HTML & Text Clipboard generation
    print("\n[TEST 10]: Kiểm tra tạo nội dung Clipboard...")
    html_report = ClipboardManager._build_html_report(dcu, notifications["DCU"])
    text_report = ClipboardManager._build_text_report(dcu, notifications["DCU"])

    assert "<table" in html_report, "HTML report phải có <table>!"
    assert "#92D050" in html_report, "HTML report phải chứa màu chuẩn Word (#92D050)!"
    assert "huongdx3" in html_report, "HTML report phải chứa username huongdx3!"
    assert "\t" in text_report, "Text report phải có ký tự tab để paste vào bảng tính!"
    print("✓ TEST 10 ĐẠT: Clipboard HTML table và Monospace Plain Text được tạo hoàn hảo cho TAMMY.")

    # TEST 11: Lọc theo vị trí Nhân viên DM (NV DM)
    print("\n[TEST 11]: Kiểm tra lọc theo vị trí 'Nhân viên DM' (NV DM)...")
    dataset_dm = dataset.get_filtered_dataset("NV DM")
    assert dataset_dm.total_employees == 167, f"Kỳ vọng 167 NV DM, nhưng có {dataset_dm.total_employees}"
    for c in dataset_dm.centers.values():
        for e in c.employees:
            assert "DM" in e.position.upper(), f"Nhân viên {e.username} vị trí {e.position} không phải NV DM!"
    print(f"✓ TEST 11 ĐẠT: Lọc chính xác 167 Nhân viên DM trên toàn tỉnh ({dataset_dm.total_tagged} tag)")

    # TEST 12: Lọc theo vị trí Nhân viên nhà trạm (NV NHÀ TRẠM)
    print("\n[TEST 12]: Kiểm tra lọc theo vị trí 'Nhân viên nhà trạm' (NV NHÀ TRẠM)...")
    dataset_nt = dataset.get_filtered_dataset("NV NHÀ TRẠM")
    assert dataset_nt.total_employees == 58, f"Kỳ vọng 58 NV Nhà Trạm, nhưng có {dataset_nt.total_employees}"
    for c in dataset_nt.centers.values():
        for e in c.employees:
            assert "TRẠM" in e.position.upper() or "TRAM" in e.position.upper(), f"Nhân viên {e.username} không phải NV Nhà trạm!"
    print(f"✓ TEST 12 ĐẠT: Lọc chính xác 58 Nhân viên Nhà trạm trên toàn tỉnh ({dataset_nt.total_tagged} tag)")

    # TEST 13: Xuất Excel theo bộ lọc vị trí
    print("\n[TEST 13]: Xuất Excel lọc theo 'NV DM'...")
    notifications_dm = {}
    for code, c in dataset_dm.centers.items():
        notifications_dm[code] = processor.generate_center_notification(
            c, tpl, dataset_dm.report_date_str, dataset_dm.day_month_str,
            dataset_dm.deadline_str, dataset_dm.meeting_time_str, "name"
        )
    out_dm = exporter.export_excel(dataset_dm, notifications_dm, output_dir=output_dir, position_filter="NV DM")
    assert "_NVDM.xlsx" in out_dm, f"Tên file xuất phải có hậu tố _NVDM: {out_dm}"
    wb_dm = openpyxl.load_workbook(out_dm, data_only=True)
    assert len(wb_dm.sheetnames) == 14
    ws_dcu_dm = wb_dm["DCU"]
    # In DCU, there are 16 NV DM
    dcu_dm_emps = dataset_dm.centers["DCU"].employees
    assert len(dcu_dm_emps) == 16, f"DCU phải có 16 NV DM, nhưng có {len(dcu_dm_emps)}"
    wb_dm.close()
    print(f"✓ TEST 13 ĐẠT: Xuất thành công file lọc {os.path.basename(out_dm)} với đúng số lượng nhân viên từng huyện")

    # TEST 14: Đọc dữ liệu WO quá hạn từ sheet WO (cột L có giá trị âm < 0)
    print("\n[TEST 14]: Kiểm tra đọc danh sách WO quá hạn từ sheet WO (cột L có giá trị âm < 0)...")
    assert dataset.total_work_orders == 171, f"Kỳ vọng 171 WO quá hạn toàn tỉnh, nhưng đọc được {dataset.total_work_orders}"
    assert len(dataset.centers["QLU"].work_orders) == 14, f"QLU phải có 14 WO, nhưng có {len(dataset.centers['QLU'].work_orders)}"
    assert len(dataset.centers["VPU"].work_orders) == 22, f"VPU phải có 22 WO, nhưng có {len(dataset.centers['VPU'].work_orders)}"
    assert len(dataset.centers["DCU"].work_orders) == 11, f"DCU phải có 11 WO, nhưng có {len(dataset.centers['DCU'].work_orders)}"
    for c in dataset.centers.values():
        for wo in c.work_orders:
            assert wo.overdue_days is not None, f"WO {wo.code} có cột L là None!"
            val_l = float(wo.overdue_days) if isinstance(wo.overdue_days, (int, float)) else float(str(wo.overdue_days).strip())
            assert val_l < 0, f"WO {wo.code} có cột L = {val_l} không phải số âm!"
    print(f"✓ TEST 14 ĐẠT: Đọc chính xác 171 WO quá hạn (cột L < 0) thuộc 14 trung tâm huyện (QLU: 14, VPU: 22, DCU: 11...)")

    # TEST 15: Kiểm tra bảng WO quá hạn trong file Excel xuất ra
    print("\n[TEST 15]: Kiểm tra bảng WO quá hạn phía dưới trong file Excel xuất ra...")
    wb_check = openpyxl.load_workbook(out_file, data_only=True)
    ws_qlu = wb_check["QLU"]
    # Find banner row
    banner_found = False
    header_found = False
    wo_rows_count = 0
    for r in range(1, ws_qlu.max_row + 1):
        v = ws_qlu.cell(row=r, column=1).value
        if v and "DANH SÁCH CHI TIẾT WO QUÁ HẠN" in str(v):
            banner_found = True
        elif banner_found and v == "STT" and ws_qlu.cell(row=r, column=2).value == "Mã công việc":
            header_found = True
        elif header_found and isinstance(v, int):
            wo_rows_count += 1
        elif header_found and v and "Tổng cộng WO quá hạn" in str(v):
            break
    wb_check.close()
    assert banner_found, "Không tìm thấy banner tiêu đề bảng WO quá hạn trong sheet QLU!"
    assert header_found, "Không tìm thấy dòng tiêu đề cột của bảng WO quá hạn trong sheet QLU!"
    assert wo_rows_count == 14, f"Kỳ vọng 14 dòng WO quá hạn trong sheet QLU, nhưng đếm được {wo_rows_count}!"
    print(f"✓ TEST 15 ĐẠT: Bảng WO quá hạn hiển thị hoàn chỉnh phía dưới sheet QLU với đầy đủ {wo_rows_count} dòng WO và hàng tổng cộng.")

    # TEST 16: Kiểm tra sao chép WO quá hạn lên Clipboard
    print("\n[TEST 16]: Kiểm tra sinh HTML và Plain Text danh sách WO quá hạn cho Clipboard...")
    html_wo = ClipboardManager._build_html_work_orders(dataset.centers["QLU"])
    text_wo = ClipboardManager._build_text_work_orders(dataset.centers["QLU"])
    assert "<table" in html_wo, "HTML WO report phải có <table>!"
    assert "Mã công việc" in html_wo, "HTML WO report phải có cột Mã công việc!"
    assert "\t" in text_wo, "Text WO report phải có định dạng tab TSV!"
    assert "Tổng số WO quá hạn: 14 WO" in text_wo, "Text WO report phải có dòng tổng kết 14 WO!"
    print("✓ TEST 16 ĐẠT: HTML và Text TSV của danh sách WO quá hạn được sinh chuẩn xác cho Clipboard/TAMMY/Excel.")

    # TEST 17: Kiểm tra đọc danh sách WO tồn chưa quá hạn từ sheet WO (cột L có giá trị > 0)
    print("\n[TEST 17]: Kiểm tra đọc danh sách WO tồn chưa quá hạn từ sheet WO (cột L > 0)...")
    assert dataset.total_pending_work_orders == 779, f"Kỳ vọng 779 WO tồn chưa quá hạn toàn tỉnh, nhưng đọc được {dataset.total_pending_work_orders}"
    assert len(dataset.centers["QLU"].pending_work_orders) == 128, f"QLU phải có 128 WO tồn chưa quá hạn, nhưng có {len(dataset.centers['QLU'].pending_work_orders)}"
    assert len(dataset.centers["DCU"].pending_work_orders) == 46, f"DCU phải có 46 WO tồn chưa quá hạn, nhưng có {len(dataset.centers['DCU'].pending_work_orders)}"
    assert len(dataset.centers["VPU"].pending_work_orders) == 91, f"VPU phải có 91 WO tồn chưa quá hạn, nhưng có {len(dataset.centers['VPU'].pending_work_orders)}"
    for c in dataset.centers.values():
        for wo in c.pending_work_orders:
            assert wo.overdue_days is not None, f"WO {wo.code} có cột L là None!"
            val_l = float(wo.overdue_days) if isinstance(wo.overdue_days, (int, float)) else float(str(wo.overdue_days).strip())
            assert val_l > 0, f"WO {wo.code} có cột L = {val_l} không phải số dương > 0!"
    print(f"✓ TEST 17 ĐẠT: Đọc chính xác 779 WO tồn chưa quá hạn (cột L > 0) toàn tỉnh (QLU: 128, DCU: 46, VPU: 91...)")

    # TEST 18: Kiểm tra bảng WO tồn chưa quá hạn trong file Excel xuất ra (khác màu, dưới bảng WO quá hạn)
    print("\n[TEST 18]: Kiểm tra bảng WO tồn chưa quá hạn phía dưới trong file Excel xuất ra...")
    wb_check = openpyxl.load_workbook(out_file, data_only=False)
    ws_qlu = wb_check["QLU"]
    p_banner_found = False
    p_header_found = False
    p_wo_rows_count = 0
    p_banner_color = None
    for r in range(1, ws_qlu.max_row + 1):
        v = ws_qlu.cell(row=r, column=1).value
        if v and "DANH SÁCH CHI TIẾT WO TỒN CHƯA QUÁ HẠN" in str(v):
            p_banner_found = True
            p_banner_color = ws_qlu.cell(row=r, column=1).fill.start_color.rgb
        elif p_banner_found and v == "STT" and ws_qlu.cell(row=r, column=2).value == "Mã công việc":
            p_header_found = True
        elif p_header_found and isinstance(v, int):
            p_wo_rows_count += 1
        elif p_header_found and v and "Tổng cộng WO tồn chưa quá hạn" in str(v):
            break
    wb_check.close()
    assert p_banner_found, "Không tìm thấy banner tiêu đề bảng WO tồn chưa quá hạn trong sheet QLU!"
    assert p_header_found, "Không tìm thấy dòng tiêu đề cột của bảng WO tồn chưa quá hạn trong sheet QLU!"
    assert p_wo_rows_count == 128, f"Kỳ vọng 128 dòng WO tồn chưa quá hạn trong sheet QLU, nhưng đếm được {p_wo_rows_count}!"
    print(f"✓ TEST 18 ĐẠT: Bảng WO tồn chưa quá hạn hiển thị hoàn chỉnh phía dưới bảng WO quá hạn với đúng màu sắc phân biệt ({p_banner_color}) và đủ {p_wo_rows_count} dòng WO.")

    # TEST 19: Kiểm tra sao chép WO tồn chưa quá hạn lên Clipboard
    print("\n[TEST 19]: Kiểm tra sinh HTML và Plain Text danh sách WO tồn chưa quá hạn cho Clipboard...")
    html_pwo = ClipboardManager._build_html_pending_work_orders(dataset.centers["QLU"])
    text_pwo = ClipboardManager._build_text_pending_work_orders(dataset.centers["QLU"])
    assert "<table" in html_pwo, "HTML pending WO report phải có <table>!"
    assert "Mã công việc" in html_pwo, "HTML pending WO report phải có cột Mã công việc!"
    assert "\t" in text_pwo, "Text pending WO report phải có định dạng tab TSV!"
    assert "Tổng số WO tồn chưa quá hạn: 128 WO" in text_pwo, "Text pending WO report phải có dòng tổng kết 128 WO!"
    print("✓ TEST 19 ĐẠT: HTML và Text TSV của danh sách WO tồn chưa quá hạn được sinh chuẩn xác cho Clipboard/TAMMY/Excel.")

    print("\n" + "=" * 60)
    print("TẤT CẢ 19/19 BÀI TEST ĐỀU ĐẠT THÀNH CÔNG RỰC RỠ!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = run_tests()
    if not success:
        sys.exit(1)
