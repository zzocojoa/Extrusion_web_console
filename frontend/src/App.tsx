import { useState } from "react";

import { AppShell } from "./components/app/AppShell";
import { DashboardPage } from "./pages/DashboardPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { LogsPage } from "./pages/LogsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { UploadPage, type UploadPageTab } from "./pages/UploadPage";
import type { AppPage } from "./components/app/navItems";
import type { DashboardOverallAction } from "./pages/dashboard/dashboardTypes";

export default function App() {
  const [activePage, setActivePage] = useState<AppPage>("dashboard");
  const [requestedUploadTab, setRequestedUploadTab] = useState<UploadPageTab>("preview");

  function navigate(page: AppPage) {
    if (page === "upload") setRequestedUploadTab("preview");
    setActivePage(page);
  }

  function openUploadTab(tab: UploadPageTab) {
    setRequestedUploadTab(tab);
    setActivePage("upload");
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
        setActivePage("logs");
        break;
      case "start_supabase":
        setActivePage("dashboard");
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
