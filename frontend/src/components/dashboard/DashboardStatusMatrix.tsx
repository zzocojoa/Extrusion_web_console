import { useTranslation } from "react-i18next";

import type { StateContext } from "../../api/stateContext";
import type { StatusMatrixItem } from "../../pages/dashboard/dashboardTypes";
import { StatusBadge } from "../status/StatusBadge";
import {
  dashboardActionLabel,
  dashboardItemDetail,
  dashboardItemLabel,
  dashboardItemValue,
  type Translate,
} from "./localizedDashboardText";

interface DashboardStatusMatrixProps {
  items: StatusMatrixItem[];
  stateContext: StateContext;
}

export function DashboardStatusMatrix({ items, stateContext }: DashboardStatusMatrixProps) {
  const { t } = useTranslation();
  const translate: Translate = (key, options) => String(t(key, options));

  return (
    <section className="dashboard-status-matrix" aria-label={t("a11y.runtimeUploadSummary")}>
      {items.map((item) => {
        const actionLabel = dashboardActionLabel(item.action, translate);
        return (
          <article className={`status-cell status-cell--${item.tone}`} key={item.id}>
            <div className="status-cell__top">
              <span className="status-cell__label">{dashboardItemLabel(item, translate)}</span>
              <StatusBadge tone={item.tone} />
            </div>
            <div className="status-cell__value">{dashboardItemValue(item, stateContext, translate)}</div>
            <div className="status-cell__detail">{dashboardItemDetail(item, stateContext, translate)}</div>
            {item.action?.href ? (
              <a
                className="status-cell__link"
                href={item.action.href}
                target={item.action.target}
                rel={item.action.target === "_blank" ? "noreferrer" : undefined}
              >
                {actionLabel ?? item.action.label}
              </a>
            ) : null}
          </article>
        );
      })}
    </section>
  );
}
