import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Circle,
  CircleX,
  LoaderCircle,
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
  busy?: boolean;
}

export function StatusBadge({ tone, label, busy = false }: StatusBadgeProps) {
  const { t } = useTranslation();
  const Icon = busy ? LoaderCircle : statusIcon[tone];
  const visibleLabel = label ?? t(`status.${tone}`);

  return (
    <span className={`status-badge status-badge--${tone}${busy ? " status-badge--busy" : ""}`} aria-label={visibleLabel}>
      <Icon aria-hidden="true" className={`status-badge__icon${busy ? " status-badge__icon--spin" : ""}`} />
      <span>{visibleLabel}</span>
    </span>
  );
}
