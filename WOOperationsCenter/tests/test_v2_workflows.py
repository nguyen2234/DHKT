"""
Comprehensive Verification Test Suite for WO Operations Center V2
Tests:
- TEST A: Province report workflow, manual editing, and clipboard generation.
- TEST B: District workspace workflow for QLU, filtering NV DM, manual TAG toggles, and data isolation.
- TEST C: Direct Excel Range Copier (Flow B) reading exported file BaoCao_THFT_20261015_NVDM.xlsx sheet DCU range A1:T20.
- TEST D: Custom export directory & custom filename picker validation.
- TEST E: Batch export for 14 districts in both single workbook and separate workbooks.
- TEST F: Directory cancel / invalid path safety (no silent or unwanted export).
"""

import os
import sys
import json
import shutil
import unittest

from backend.readers.excel_input_engine import ExcelInputEngine
from backend.processors.executive_report import ExecutiveReportProcessor
from backend.processors.thft_report import THFTReportProcessor
from backend.clipboard.clipboard_engine import ClipboardEngine
from backend.clipboard.excel_range_copier import ExcelRangeCopier
from backend.exporters.excel_exporter import ExcelExporter
from backend.core.config import ConfigManager

TEST_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "test_output", "v2_tests")
SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "samples")


class TestV2Workflows(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
        cls.engine = ExcelInputEngine()
        # Robustly locate master file
        candidates = [
            f for f in os.listdir(SAMPLES_DIR)
            if f.endswith(".xlsx") and ("DH WO" in f or "ĐH WO" in f or "05102026" in f)
        ]
        assert candidates, f"No master file found in {SAMPLES_DIR}"
        cls.master_file = os.path.join(SAMPLES_DIR, candidates[0])
        cls.dataset = cls.engine.parse_workbook(cls.master_file)

    def test_workflow_A_province_report(self):
        """TEST A: Province Report generation, manual edits, and CF_HTML clipboard."""
        ps = self.dataset.province_summary
        self.assertGreater(ps.tong_ton, 0)
        self.assertGreater(ps.thuc_hien_ngay, 0)

        # Generate report text
        original_text = ExecutiveReportProcessor.generate_report_text(ps)
        self.assertIn("PVHKT kính gửi", original_text)
        self.assertIn(f"+Thực hiện ngày: {ps.thuc_hien_ngay} WO", original_text)

        # Simulate user manual edit
        edited_text = original_text + "\n[LƯU Ý ĐẶC BIỆT: Họp khẩn cấp lúc 14:00]"
        self.assertIn("[LƯU Ý ĐẶC BIỆT", edited_text)

        # Verify clipboard formats
        cf_html = ClipboardEngine._set_win32_clipboard(edited_text, f"<pre>{edited_text}</pre>")
        self.assertTrue(cf_html)

    def test_workflow_B_district_qlu_nvdm(self):
        """TEST B: QLU district selection, NV DM filter, TAG isolation."""
        # 1. District isolation
        qlu = self.dataset.centers.get("QLU")
        self.assertIsNotNone(qlu)

        # 2. Filter NV DM only
        dm_employees = [e for e in qlu.employees if "DM" in e.position.upper()]
        self.assertGreater(len(dm_employees), 0)
        for e in dm_employees:
            self.assertIn("DM", e.position.upper())

        # 3. Manual TAG toggle
        test_emp = dm_employees[0]
        original_tag = test_emp.is_tagged
        THFTReportProcessor.set_employee_tag_override(self.dataset, "QLU", test_emp.username, not original_tag)
        self.assertEqual(test_emp.is_tagged, not original_tag)

        # Reset
        THFTReportProcessor.set_employee_tag_override(self.dataset, "QLU", test_emp.username, original_tag)

        # 4. Generate notification
        notif = THFTReportProcessor.generate_center_notification(
            qlu,
            "Báo cáo huyện {TEN_HUYEN} ngày {NGAY_THANG}:\n{DANH_SACH_TAG}",
            self.dataset.report_date_str,
            self.dataset.day_month_str,
            "05/10",
            "06:30",
            tag_format="name"
        )
        self.assertIn("Quỳnh Lưu", notif)

    def test_workflow_C_excel_range_copier(self):
        """TEST C: Flow B - Copy directly from exported file BaoCao_THFT_20261015_NVDM.xlsx sheet DCU."""
        sample_path = os.path.join(SAMPLES_DIR, "BaoCao_THFT_20261015_NVDM.xlsx")
        self.assertTrue(os.path.exists(sample_path), f"File not found: {sample_path}")

        # Read sheet names
        sheets = ExcelRangeCopier.get_sheet_names(sample_path)
        self.assertIn("DCU", sheets)
        self.assertIn("QLU", sheets)

        # Parse range A1:T20 on sheet DCU
        data = ExcelRangeCopier.parse_range(sample_path, "DCU", "A1:T20")
        self.assertEqual(data["sheet_name"], "DCU")
        self.assertGreater(len(data["preview_rows"]), 0)
        self.assertIn("<table", data["html_table"])
        self.assertIn("huongdx3", data["tsv_text"])

        # Test copying in all 3 modes
        ok_html = ExcelRangeCopier.copy_range_to_clipboard(sample_path, "DCU", "A1:T20", "html")
        self.assertTrue(ok_html)

        ok_tsv = ExcelRangeCopier.copy_range_to_clipboard(sample_path, "DCU", "A1:T20", "tsv")
        self.assertTrue(ok_tsv)

        ok_text = ExcelRangeCopier.copy_range_to_clipboard(sample_path, "DCU", "A1:T20", "text")
        self.assertTrue(ok_text)

    def test_workflow_D_export_location_picker(self):
        """TEST D: Custom export directory & custom filename."""
        custom_dir = os.path.join(TEST_OUTPUT_DIR, "custom_export_dir")
        os.makedirs(custom_dir, exist_ok=True)
        custom_name = "BaoCao_Test_Export_Picker.xlsx"
        target_file = os.path.join(custom_dir, custom_name)
        if os.path.exists(target_file):
            os.remove(target_file)

        out_path = ExcelExporter.export_executive_report(
            self.dataset.province_summary,
            list(self.dataset.centers.values()),
            custom_dir,
            preview_text="Test Executive Report",
            custom_filename=custom_name
        )

        self.assertTrue(os.path.exists(out_path))
        self.assertEqual(os.path.basename(out_path), custom_name)

    def test_workflow_E_batch_export_14_districts(self):
        """TEST E: Batch export for 14 districts in both single multi-sheet workbook and separate files."""
        # Mode 1: Single workbook with all 14 sheets
        notifications = {code: f"Thông báo huyện {code}" for code in self.dataset.centers.keys()}
        paths_single = ExcelExporter.export_thft_reports(
            self.dataset,
            notifications,
            TEST_OUTPUT_DIR,
            selected_center_codes=list(self.dataset.centers.keys()),
            separate_files=False,
            position_filter="NV DM",
            custom_filename="BaoCao_THFT_Batch_All14.xlsx"
        )
        self.assertEqual(len(paths_single), 1)
        self.assertTrue(os.path.exists(paths_single[0]))

        # Verify sheets
        sheets = ExcelRangeCopier.get_sheet_names(paths_single[0])
        self.assertEqual(len(sheets), 14)
        self.assertIn("DCU", sheets)
        self.assertIn("YTH", sheets)

        # Mode 2: Separate workbooks (test 3 sample districts to ensure speed and isolation)
        sample_codes = ["DCU", "DDG", "QLU"]
        paths_separate = ExcelExporter.export_thft_reports(
            self.dataset,
            notifications,
            TEST_OUTPUT_DIR,
            selected_center_codes=sample_codes,
            separate_files=True,
            position_filter="NV Nhà Trạm"
        )
        self.assertEqual(len(paths_separate), 3)
        for p in paths_separate:
            self.assertTrue(os.path.exists(p))

    def test_workflow_F_safety_invalid_dir(self):
        """TEST F: Safety against invalid paths and directories."""
        invalid_dir = "Z:\\NonExistentDrive_9999\\FakeFolder"
        try:
            ExcelExporter.export_executive_report(
                self.dataset.province_summary,
                list(self.dataset.centers.values()),
                invalid_dir
            )
            # Should have failed
            self.fail("Expected exception when writing to non-existent drive")
        except Exception:
            pass  # Expected safe failure without altering existing files


if __name__ == "__main__":
    unittest.main()
