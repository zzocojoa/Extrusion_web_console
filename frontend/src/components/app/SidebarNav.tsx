import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { useTranslation } from "react-i18next";

import type { AppPage } from "./navItems";
import { navItems } from "./navItems";

interface SidebarNavProps {
  activePage: AppPage;
  collapsed: boolean;
  mobileOpen: boolean;
  onCloseMobile: () => void;
  onNavigate: (page: AppPage) => void;
  onToggleCollapsed: () => void;
}

export function SidebarNav({
  activePage,
  collapsed,
  mobileOpen,
  onCloseMobile,
  onNavigate,
  onToggleCollapsed,
}: SidebarNavProps) {
  const { t, i18n } = useTranslation();
  const nextLanguage = i18n.language === "ko" ? "en" : "ko";
  const CollapseIcon = collapsed ? PanelLeftOpen : PanelLeftClose;

  function changeLanguage() {
    if (typeof window !== "undefined") {
      window.localStorage.setItem("ewc.language", nextLanguage);
    }
    void i18n.changeLanguage(nextLanguage);
  }

  return (
    <aside className={`sidebar ${collapsed ? "sidebar--collapsed" : ""} ${mobileOpen ? "sidebar--open" : ""}`} aria-label={t("a11y.primaryNavigation")}>
      <div className="sidebar__brand">
        <img
          className="sidebar__brand-mark"
          src="/brand/logo-mark.png"
          alt=""
          aria-hidden="true"
        />
        <img
          className="sidebar__brand-lockup"
          src="/brand/logo-sidebar.png"
          alt={t("app.name")}
        />
        <button
          aria-label={collapsed ? t("appShell.expandNavigation") : t("appShell.collapseNavigation")}
          className="icon-button sidebar__collapse-button"
          type="button"
          onClick={onToggleCollapsed}
        >
          <CollapseIcon size={18} aria-hidden="true" />
        </button>
        <button
          aria-label={t("appShell.closeNavigation")}
          className="icon-button sidebar__mobile-close"
          type="button"
          onClick={onCloseMobile}
        >
          <PanelLeftClose size={18} aria-hidden="true" />
        </button>
      </div>

      <nav className="sidebar__nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activePage === item.id;
          return (
            <button
              key={item.id}
              type="button"
              className="sidebar__nav-item"
              aria-current={isActive ? "page" : undefined}
              aria-label={t(item.labelKey)}
              title={t(item.labelKey)}
              onClick={() => onNavigate(item.id)}
            >
              <Icon aria-hidden="true" size={16} />
              <span>{t(item.labelKey)}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar__meta">
        <span className="status-badge status-badge--ready">{t("app.localhost")}</span>
        <button
          className="language-button"
          type="button"
          onClick={changeLanguage}
        >
          {nextLanguage === "en" ? "English" : "한국어"}
        </button>
        <span className="sidebar__version">{t("app.version")}</span>
      </div>
    </aside>
  );
}
