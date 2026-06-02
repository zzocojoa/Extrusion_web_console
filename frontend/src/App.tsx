import { useState } from "react";

import { AppShell } from "./components/app/AppShell";
import { DashboardPage } from "./pages/DashboardPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { SettingsPage } from "./pages/SettingsPage";
import { UploadPage } from "./pages/UploadPage";
import type { AppPage } from "./components/app/navItems";

export default function App() {
  const [activePage, setActivePage] = useState<AppPage>("dashboard");

  return (
    <AppShell activePage={activePage} onNavigate={setActivePage}>
      {activePage === "dashboard" ? (
        <DashboardPage />
      ) : activePage === "upload" ? (
        <UploadPage />
      ) : activePage === "settings" ? (
        <SettingsPage />
      ) : (
        <PlaceholderPage page={activePage} />
      )}
    </AppShell>
  );
}
