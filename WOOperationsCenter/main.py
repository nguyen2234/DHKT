"""
WO Operations Center — Main Desktop Application Entrypoint.
Merges WO Reporting Tool and THFT Report Tool into one unified, production-ready
Windows desktop operations center using PySide6 and Qt WebEngine.
"""

import logging
import os
import sys
from pathlib import Path

from PySide6.QtCore import QDir, QUrl
from PySide6.QtGui import QIcon
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QMainWindow

from backend.bridge.api_bridge import APIBridge
from backend.core.config import get_logs_dir

# Setup logging
log_file = get_logs_dir() / "wo_operations_center.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(str(log_file), encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("WOOperationsCenter")


class MainWindow(QMainWindow):
    """Main application window hosting the React UI inside Qt WebEngine."""

    def __init__(self, dev_mode: bool = False):
        super().__init__()
        self.dev_mode = dev_mode

        self.setWindowTitle("WO Operations Center — Trung Tâm Điều Hành WO")
        self.resize(1360, 860)
        self.setMinimumSize(1024, 680)

        # Set Application Icon
        icon_path = Path(__file__).parent / "packaging" / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # WebEngine View
        self.view = QWebEngineView(self)
        self.setCentralWidget(self.view)

        # Configure WebEngine Settings
        settings = self.view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)

        # Setup Qt WebChannel
        self.channel = QWebChannel(self.view.page())
        self.bridge = APIBridge(self)
        self.channel.registerObject("pyBridge", self.bridge)
        self.view.page().setWebChannel(self.channel)

        # Load UI
        self._load_ui()

    def _load_ui(self):
        """Loads either the Vite dev server or the production build."""
        dev_url = os.environ.get("WO_DEV_URL")
        if self.dev_mode or dev_url:
            target_url = dev_url or "http://localhost:5173"
            logger.info(f"Loading UI from Vite development server: {target_url}")
            self.view.load(QUrl(target_url))
        else:
            # Production dist path
            base_dir = Path(__file__).parent
            dist_index = base_dir / "frontend" / "dist" / "index.html"

            if dist_index.exists():
                logger.info(f"Loading UI from production bundle: {dist_index}")
                self.view.load(QUrl.fromLocalFile(str(dist_index.resolve())))
            else:
                logger.warning(f"Production bundle not found at {dist_index}. Trying dev server...")
                self.view.load(QUrl("http://localhost:5173"))


def main():
    """Main application bootstrap."""
    # High DPI scaling
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("WO Operations Center")
    app.setOrganizationName("NAN_DHKT")

    dev_flag = "--dev" in sys.argv
    window = MainWindow(dev_mode=dev_flag)
    window.show()

    logger.info("Application started.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
