import type { PropsWithChildren } from "react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { SidebarNav } from "./SidebarNav";
import { TopStatusBar } from "./TopStatusBar";
import type { AppPage } from "./navItems";

interface AppShellProps extends PropsWithChildren {
  activePage: AppPage;
  onNavigate: (page: AppPage) => void;
}

const sidebarCollapsedStorageKey = "ewc.ui.sidebarCollapsed.v1";

export function AppShell({ activePage, onNavigate, children }: AppShellProps) {
  const { t } = useTranslation();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => readSidebarCollapsed());
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(sidebarCollapsedStorageKey, sidebarCollapsed ? "true" : "false");
  }, [sidebarCollapsed]);

  useEffect(() => {
    if (!mobileSidebarOpen) return;
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setMobileSidebarOpen(false);
    }
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [mobileSidebarOpen]);

  function navigate(page: AppPage) {
    onNavigate(page);
    setMobileSidebarOpen(false);
  }

  return (
    <div className={`app-shell ${sidebarCollapsed ? "app-shell--sidebar-collapsed" : ""}`}>
      <SidebarNav
        activePage={activePage}
        collapsed={sidebarCollapsed}
        mobileOpen={mobileSidebarOpen}
        onCloseMobile={() => setMobileSidebarOpen(false)}
        onNavigate={navigate}
        onToggleCollapsed={() => setSidebarCollapsed((value) => !value)}
      />
      {mobileSidebarOpen ? (
        <button
          aria-label={t("appShell.closeNavigation")}
          className="sidebar-backdrop"
          type="button"
          onClick={() => setMobileSidebarOpen(false)}
        />
      ) : null}
      <TopStatusBar
        sidebarCollapsed={sidebarCollapsed}
        title={t(`nav.${activePage}`)}
        onOpenMobileNavigation={() => setMobileSidebarOpen(true)}
        onToggleSidebarCollapsed={() => setSidebarCollapsed((value) => !value)}
      />
      {children}
    </div>
  );
}

function readSidebarCollapsed() {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(sidebarCollapsedStorageKey) === "true";
}
