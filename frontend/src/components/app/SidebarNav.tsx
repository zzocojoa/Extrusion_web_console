import { useTranslation } from "react-i18next";

import type { AppPage } from "./navItems";
import { navItems } from "./navItems";

interface SidebarNavProps {
  activePage: AppPage;
  onNavigate: (page: AppPage) => void;
}

export function SidebarNav({ activePage, onNavigate }: SidebarNavProps) {
  const { t, i18n } = useTranslation();

  return (
    <aside className="sidebar" aria-label="Primary navigation">
      <div className="sidebar__brand">
        <span className="sidebar__product">{t("app.name")}</span>
        <span className="sidebar__subtitle">{t("app.subtitle")}</span>
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
          onClick={() => i18n.changeLanguage(i18n.language === "ko" ? "en" : "ko")}
        >
          {i18n.language === "ko" ? "English" : "한국어"}
        </button>
        <span className="sidebar__version">{t("app.version")}</span>
      </div>
    </aside>
  );
}
