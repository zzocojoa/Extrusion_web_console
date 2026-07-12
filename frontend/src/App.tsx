import { useEffect, useState } from "react";

import { pageFromPathname, pathnameForPage } from "./appRouting";
import { AppShell } from "./components/app/AppShell";
import { DashboardPage } from "./pages/DashboardPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { LogsPage } from "./pages/LogsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { UploadPage, type UploadPageTab } from "./pages/UploadPage";
import type { AppPage } from "./components/app/navItems";
import type { DashboardOverallAction } from "./pages/dashboard/dashboardTypes";

export default function App() {
  const [activePage, setActivePage] = useState<AppPage>(() => pageFromPathname(window.location.pathname));
  const [requestedUploadTab, setRequestedUploadTab] = useState<UploadPageTab>("preview");

  useEffect(() => {
    function handlePopState() {
      const page = pageFromPathname(window.location.pathname);
      if (page === "upload") setRequestedUploadTab("preview");
      setActivePage(page);
    }

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  function activatePage(page: AppPage) {
    const pathname = pathnameForPage(page);
    if (window.location.pathname !== pathname) window.history.pushState(null, "", pathname);
    setActivePage(page);
  }

  function navigate(page: AppPage) {
    if (page === "upload") setRequestedUploadTab("preview");
    activatePage(page);
  }

  function openUploadTab(tab: UploadPageTab) {
    setRequestedUploadTab(tab);
    activatePage("upload");
  }

  function handleDashboardSafetyAction(action: DashboardOverallAction) {
    switch (action) {
      case "preview":
      case "start_upload":
        openUploadTab("preview");
        break;
      case "open_job":
      case "retry_failed":
        openUploadTab("job");
        break;
      case "open_logs":
        activatePage("logs");
        break;
      case "start_supabase":
        activatePage("dashboard");
        break;
    }
  }

  return (
    <AppShell activePage={activePage} onNavigate={navigate}>
      {activePage === "dashboard" ? (
        <DashboardPage onSafetyAction={handleDashboardSafetyAction} />
      ) : activePage === "upload" ? (
        <UploadPage requestedTab={requestedUploadTab} />
      ) : activePage === "logs" ? (
        <LogsPage />
      ) : activePage === "settings" ? (
        <SettingsPage />
      ) : (
        <PlaceholderPage page={activePage} />
      )}
    </AppShell>
  );
}
