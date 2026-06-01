import { useTranslation } from "react-i18next";

import type { AppPage } from "../components/app/navItems";

interface PlaceholderPageProps {
  page: Exclude<AppPage, "dashboard">;
}

export function PlaceholderPage({ page }: PlaceholderPageProps) {
  const { t } = useTranslation();

  return (
    <main className="dashboard-page placeholder-page" aria-labelledby="dashboard-title">
      <section className="panel placeholder-panel">
        <div className="panel__header">
          <h2>{t(`nav.${page}`)}</h2>
        </div>
        <p>{t(`placeholder.${page}`)}</p>
      </section>
    </main>
  );
}
