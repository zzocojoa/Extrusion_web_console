import { useTranslation } from "react-i18next";

import type { StateContext } from "../../api/stateContext";
import { unknownStateContext } from "../../api/stateContext";
import { dashboardChipLabel, dashboardChipValue, type Translate } from "../dashboard/localizedDashboardText";
import type { TopbarStatusChip } from "../../pages/dashboard/dashboardTypes";
import { StatusBadge } from "./StatusBadge";

interface StatusChipGroupProps {
  chips: TopbarStatusChip[];
  stateContext?: StateContext;
}

export function StatusChipGroup({ chips, stateContext = unknownStateContext }: StatusChipGroupProps) {
  const { t } = useTranslation();
  const translate: Translate = (key, options) => String(t(key, options));

  return (
    <div className="topbar__status" aria-label={t("a11y.systemStatus")} aria-live="polite">
      {chips.map((chip) => (
        <span className="status-chip" key={chip.id}>
          <span className="status-chip__label">{dashboardChipLabel(chip, translate)}</span>
          <StatusBadge tone={chip.tone} label={dashboardChipValue(chip, stateContext, translate)} />
        </span>
      ))}
    </div>
  );
}
