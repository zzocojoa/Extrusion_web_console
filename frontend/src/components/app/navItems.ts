import { BarChart3, FileUp, Settings, ScrollText, type LucideIcon } from "lucide-react";

export type AppPage = "dashboard" | "upload" | "logs" | "settings";

export interface NavItem {
  id: AppPage;
  labelKey: string;
  icon: LucideIcon;
}

export const navItems: NavItem[] = [
  { id: "dashboard", labelKey: "nav.dashboard", icon: BarChart3 },
  { id: "upload", labelKey: "nav.upload", icon: FileUp },
  { id: "logs", labelKey: "nav.logs", icon: ScrollText },
  { id: "settings", labelKey: "nav.settings", icon: Settings },
];
