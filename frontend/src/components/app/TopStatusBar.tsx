import { Menu, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useDashboardQuery } from "../../pages/dashboard/dashboardQuery";
import { StatusChipGroup } from "../status/StatusChipGroup";

interface TopStatusBarProps {
  sidebarCollapsed: boolean;
  title: string;
  subtitle: string;
  onOpenMobileNavigation: () => void;
  onToggleSidebarCollapsed: () => void;
}

export function TopStatusBar({
  sidebarCollapsed,
  title,
  subtitle,
  onOpenMobileNavigation,
  onToggleSidebarCollapsed,
}: TopStatusBarProps) {
  const { t } = useTranslation();
  const { data } = useDashboardQuery();
  const CollapseIcon = sidebarCollapsed ? PanelLeftOpen : PanelLeftClose;

  return (
    <header className="topbar">
      <div className="topbar__nav-actions">
        <button
          aria-label={t("appShell.openNavigation")}
          className="icon-button topbar__menu-button"
          type="button"
          onClick={onOpenMobileNavigation}
        >
          <Menu size={18} aria-hidden="true" />
        </button>
        <button
          aria-label={sidebarCollapsed ? t("appShell.expandNavigation") : t("appShell.collapseNavigation")}
          className="icon-button topbar__collapse-button"
          type="button"
          onClick={onToggleSidebarCollapsed}
        >
          <CollapseIcon size={18} aria-hidden="true" />
        </button>
      </div>
      <div className="topbar__title">
        <h1 id="dashboard-title">{title}</h1>
        <p>{subtitle}</p>
      </div>
      <StatusChipGroup chips={data?.topbarChips ?? []} stateContext={data?.stateContext} />
    </header>
  );
}
