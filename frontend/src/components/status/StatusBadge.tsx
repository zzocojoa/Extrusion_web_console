import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Circle,
  CircleX,
  OctagonAlert,
  TriangleAlert,
  type LucideIcon,
} from "lucide-react";
import { useTranslation } from "react-i18next";

import type { StatusTone } from "../../pages/dashboard/dashboardTypes";

const statusIcon: Record<StatusTone, LucideIcon> = {
  ready: CheckCircle,
  running: Activity,
  attention: TriangleAlert,
  risk: AlertTriangle,
  failed: CircleX,
  blocked: OctagonAlert,
  muted: Circle,
};

interface StatusBadgeProps {
  tone: StatusTone;
  label?: string;
}

export function StatusBadge({ tone, label }: StatusBadgeProps) {
  const { t } = useTranslation();
  const Icon = statusIcon[tone];
  const visibleLabel = label ?? t(`status.${tone}`);

  return (
    <span className={`status-badge status-badge--${tone}`} aria-label={visibleLabel}>
      <Icon aria-hidden="true" className="status-badge__icon" />
      <span>{visibleLabel}</span>
    </span>
  );
}
