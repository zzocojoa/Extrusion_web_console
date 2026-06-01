import { useTranslation } from "react-i18next";

import type { TopbarStatusChip } from "../../pages/dashboard/dashboardTypes";
import { StatusBadge } from "./StatusBadge";

interface StatusChipGroupProps {
  chips: TopbarStatusChip[];
}

export function StatusChipGroup({ chips }: StatusChipGroupProps) {
  const { t } = useTranslation();

  return (
    <div className="topbar__status" aria-label={t("a11y.systemStatus")} aria-live="polite">
      {chips.map((chip) => (
        <span className="status-chip" key={chip.id}>
          <span className="status-chip__label">{chip.label}</span>
          <StatusBadge tone={chip.tone} label={chip.value} />
        </span>
      ))}
    </div>
  );
}
