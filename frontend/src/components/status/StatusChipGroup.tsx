import type { TopbarStatusChip } from "../../pages/dashboard/dashboardTypes";
import { StatusBadge } from "./StatusBadge";

interface StatusChipGroupProps {
  chips: TopbarStatusChip[];
}

export function StatusChipGroup({ chips }: StatusChipGroupProps) {
  return (
    <div className="topbar__status" aria-label="System status">
      {chips.map((chip) => (
        <span className="status-chip" key={chip.id}>
          <span className="status-chip__label">{chip.label}</span>
          <StatusBadge tone={chip.tone} label={chip.value} />
        </span>
      ))}
    </div>
  );
}
