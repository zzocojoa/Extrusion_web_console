import type { PropsWithChildren } from "react";
import { useTranslation } from "react-i18next";

import { SidebarNav } from "./SidebarNav";
import { TopStatusBar } from "./TopStatusBar";
import type { AppPage } from "./navItems";

interface AppShellProps extends PropsWithChildren {
  activePage: AppPage;
  onNavigate: (page: AppPage) => void;
}

export function AppShell({ activePage, onNavigate, children }: AppShellProps) {
  const { t } = useTranslation();

  return (
    <div className="app-shell">
      <SidebarNav activePage={activePage} onNavigate={onNavigate} />
      <TopStatusBar title={t(`nav.${activePage}`)} subtitle={t(`pageSubtitle.${activePage}`)} />
      {children}
    </div>
  );
}
