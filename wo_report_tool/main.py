"""
Application Entry Point for WO Report Tool.
Executable launcher for Windows Desktop.
"""

import logging
import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from app.config import get_base_directory
from app.main_window import MainWindow
from app.utils import setup_logging

logger = logging.getLogger("main")


def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    """Global exception hook to prevent silent crashes and log error details."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("Uncaught Exception encountered:", exc_info=(exc_type, exc_value, exc_traceback))
    try:
        QMessageBox.critical(
            None,
            "Lỗi nghiêm trọng",
            f"Đã xảy ra lỗi ngoài ý muốn:\n{str(exc_value)}\n\nChi tiết xem trong file log."
        )
    except Exception:
        pass


def main():
    # Setup global logging
    setup_logging()
    logger.info("Starting WO Report Tool Application...")

    sys.excepthook = handle_uncaught_exception

    # High DPI scaling attributes for Windows 10/11
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("CÔNG CỤ TẠO BÁO CÁO WO")
    app.setOrganizationName("NAN_DHKT")

    # Set default clean font
    app.setFont(QFont("Segoe UI", 10))

    # Set Application Icon
    icon_path = os.path.join(get_base_directory(), "assets", "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
