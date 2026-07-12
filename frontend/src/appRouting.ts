import type { AppPage } from "./components/app/navItems";

const pageByPathname: Readonly<Record<string, AppPage>> = {
  "/": "dashboard",
  "/upload": "upload",
  "/logs": "logs",
  "/settings": "settings",
};

const pathnameByPage: Readonly<Record<AppPage, string>> = {
  dashboard: "/",
  upload: "/upload",
  logs: "/logs",
  settings: "/settings",
};

export function pageFromPathname(pathname: string): AppPage {
  const normalized = pathname.length > 1 ? pathname.replace(/\/+$/, "") : pathname;
  return pageByPathname[normalized] ?? "dashboard";
}

export function pathnameForPage(page: AppPage): string {
  return pathnameByPage[page];
}
