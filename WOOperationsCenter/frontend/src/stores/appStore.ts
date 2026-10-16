import { create } from "zustand";
import { DatasetSummary } from "../services/bridge";

export type AppRoute =
  | "dashboard"
  | "import"
  | "wo-executive"
  | "thft"
  | "wo-explorer"
  | "centers"
  | "center-detail"
  | "report-builder"
  | "history"
  | "settings"
  | "design-system";

export interface ToastMessage {
  id: string;
  type: "success" | "error" | "info" | "warning";
  title?: string;
  message: string;
}

interface AppState {
  theme: "light" | "dark";
  sidebarCollapsed: boolean;
  currentRoute: AppRoute;
  selectedCenterCode: string | null;
  positionFilter: string;
  dataset: DatasetSummary | null;
  isLoading: boolean;
  loadingProgress: { pct: number; msg: string } | null;
  toasts: ToastMessage[];

  setTheme: (theme: "light" | "dark") => void;
  toggleTheme: () => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setCurrentRoute: (route: AppRoute, centerCode?: string) => void;
  setSelectedCenterCode: (code: string | null) => void;
  setPositionFilter: (filter: string) => void;
  setDataset: (dataset: DatasetSummary | null) => void;
  setLoading: (isLoading: boolean, progress?: { pct: number; msg: string } | null) => void;
  addToast: (toast: Omit<ToastMessage, "id">) => void;
  removeToast: (id: string) => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  theme: "light",
  sidebarCollapsed: false,
  currentRoute: "dashboard",
  selectedCenterCode: null,
  positionFilter: "Tất cả",
  dataset: null,
  isLoading: false,
  loadingProgress: null,
  toasts: [],

  setTheme: (theme) => {
    set({ theme });
    if (typeof document !== "undefined") {
      document.documentElement.classList.remove("light", "dark");
      document.documentElement.classList.add(theme);
    }
  },

  toggleTheme: () => {
    const nextTheme = get().theme === "light" ? "dark" : "light";
    get().setTheme(nextTheme);
  },

  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),

  setCurrentRoute: (currentRoute, centerCode) => {
    if (centerCode) {
      set({ currentRoute, selectedCenterCode: centerCode });
    } else {
      set({ currentRoute });
    }
  },

  setSelectedCenterCode: (selectedCenterCode) => set({ selectedCenterCode }),
  setPositionFilter: (positionFilter) => set({ positionFilter }),
  setDataset: (dataset) => set({ dataset }),
  setLoading: (isLoading, progress = null) => set({ isLoading, loadingProgress: progress }),

  addToast: (toast) => {
    const id = Math.random().toString(36).substring(2, 9);
    set((s) => ({ toasts: [...s.toasts, { ...toast, id }] }));
    setTimeout(() => {
      get().removeToast(id);
    }, 4000);
  },

  removeToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }))
}));
