import React, { useEffect } from "react";
import { useAppStore } from "./stores/appStore";
import { bridge } from "./services/bridge";
import { Sidebar } from "./layouts/Sidebar";
import { TopBar } from "./layouts/TopBar";
import { ToastContainer } from "./components/ui/Toast";

// Pages
import { DashboardPage } from "./pages/DashboardPage";
import { ImportPage } from "./pages/ImportPage";
import { WOExecutivePage } from "./pages/WOExecutivePage";
import { THFTPage } from "./pages/THFTPage";
import { WOExplorerPage } from "./pages/WOExplorerPage";
import { CentersPage } from "./pages/CentersPage";
import { CenterDetailPage } from "./pages/CenterDetailPage";
import { ReportBuilderPage } from "./pages/ReportBuilderPage";
import { BatchReportPage } from "./pages/BatchReportPage";
import { ExcelCopierPage } from "./pages/ExcelCopierPage";
import { HistoryPage } from "./pages/HistoryPage";
import { SettingsPage } from "./pages/SettingsPage";
import { DesignSystemPage } from "./pages/DesignSystemPage";

export const App: React.FC = () => {
  const { currentRoute, setCurrentRoute, setDataset, theme, setTheme } = useAppStore();

  useEffect(() => {
    // Initial theme setup
    document.documentElement.classList.add(theme);

    // Initial load check for already loaded dataset or config
    bridge.getLoadedDataset().then((ds) => {
      if (ds) {
        setDataset(ds);
      }
    });

    bridge.getAppConfig().then((cfg) => {
      if (cfg && cfg.theme) {
        setTheme(cfg.theme);
      }
    });

    // Global keyboard shortcuts
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCurrentRoute("wo-explorer");
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const renderActivePage = () => {
    switch (currentRoute) {
      case "dashboard":
        return <DashboardPage />;
      case "import":
        return <ImportPage />;
      case "wo-executive":
        return <WOExecutivePage />;
      case "thft":
        return <THFTPage />;
      case "wo-explorer":
        return <WOExplorerPage />;
      case "centers":
        return <CentersPage />;
      case "center-detail":
        return <CenterDetailPage />;
      case "report-builder":
        return <ReportBuilderPage />;
      case "batch-report":
        return <BatchReportPage />;
      case "excel-copier":
        return <ExcelCopierPage />;
      case "history":
        return <HistoryPage />;
      case "settings":
        return <SettingsPage />;
      case "design-system":
        return <DesignSystemPage />;
      default:
        return <DashboardPage />;
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground">
      {/* Left Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        {/* Top Navigation Bar */}
        <TopBar />

        {/* Scrollable Page Body */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          {renderActivePage()}
        </main>
      </div>

      {/* Global Toast Notifications */}
      <ToastContainer />
    </div>
  );
};

export default App;
