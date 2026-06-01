import type { StatusMatrixItem } from "../../pages/dashboard/dashboardTypes";
import { StatusBadge } from "../status/StatusBadge";

interface DashboardStatusMatrixProps {
  items: StatusMatrixItem[];
}

export function DashboardStatusMatrix({ items }: DashboardStatusMatrixProps) {
  return (
    <section className="dashboard-status-matrix" aria-label="Runtime and upload summary">
      {items.map((item) => (
        <article className={`status-cell status-cell--${item.tone}`} key={item.id}>
          <div className="status-cell__top">
            <span className="status-cell__label">{item.label}</span>
            <StatusBadge tone={item.tone} />
          </div>
          <div className="status-cell__value">{item.value}</div>
          <div className="status-cell__detail">{item.detail}</div>
          {item.action?.href ? (
            <a
              className="status-cell__link"
              href={item.action.href}
              target={item.action.target}
              rel={item.action.target === "_blank" ? "noreferrer" : undefined}
            >
              {item.action.label}
            </a>
          ) : null}
        </article>
      ))}
    </section>
  );
}
