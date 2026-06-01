import { useDashboardQuery } from "../../pages/dashboard/dashboardQuery";
import { StatusChipGroup } from "../status/StatusChipGroup";

interface TopStatusBarProps {
  title: string;
  subtitle: string;
}

export function TopStatusBar({ title, subtitle }: TopStatusBarProps) {
  const { data } = useDashboardQuery();

  return (
    <header className="topbar">
      <div className="topbar__title">
        <h1 id="dashboard-title">{title}</h1>
        <p>{subtitle}</p>
      </div>
      <StatusChipGroup chips={data?.topbarChips ?? []} />
    </header>
  );
}
