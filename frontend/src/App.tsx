import { useState } from "react";

import { AppShell } from "./components/app/AppShell";
import { DashboardPage } from "./pages/DashboardPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
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
      ) : (
        <PlaceholderPage page={activePage} />
      )}
    </AppShell>
  );
}
