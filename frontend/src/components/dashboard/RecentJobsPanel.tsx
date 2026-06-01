import { useTranslation } from "react-i18next";

import type { CurrentJobSummary, RecentJobRow } from "../../pages/dashboard/dashboardTypes";
import { StatusBadge } from "../status/StatusBadge";
import { Panel } from "../ui/Panel";
import { formatCount, formatKstTime, statusToneForJob } from "./formatters";

interface RecentJobsPanelProps {
  jobs: RecentJobRow[];
  currentJob: CurrentJobSummary | null;
}

export function RecentJobsPanel({ jobs, currentJob }: RecentJobsPanelProps) {
  const { t, i18n } = useTranslation();

  return (
    <Panel className="recent-jobs-panel" title={t("dashboard.jobs.title")} titleId="recent-jobs-title">
      {currentJob ? (
        <div className="current-job">
          <div>
            <span className="panel-eyebrow">{t("dashboard.jobs.current")}</span>
            <strong className="job-id">{currentJob.jobId}</strong>
          </div>
          <div className="progress">
            <div className="progress__meta">
              <span>{t("dashboard.jobs.progress")}</span>
              <span className="num">{currentJob.progressPct}%</span>
            </div>
            <div className="progress__track" aria-hidden="true">
              <span style={{ width: `${currentJob.progressPct}%` }} />
            </div>
          </div>
          <span className="current-job__message truncate">{currentJob.latestMessage}</span>
        </div>
      ) : null}
      <div className="table-scroll">
        <table className="data-table data-table--recent">
          <thead>
            <tr>
              <th scope="col">{t("dashboard.jobs.status")}</th>
              <th scope="col">{t("dashboard.jobs.started")}</th>
              <th scope="col">{t("dashboard.jobs.mode")}</th>
              <th className="num" scope="col">{t("dashboard.jobs.files")}</th>
              <th className="num" scope="col">{t("dashboard.jobs.rows")}</th>
              <th className="num" scope="col">{t("dashboard.jobs.failures")}</th>
              <th scope="col">{t("dashboard.jobs.message")}</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr className={`row--${statusToneForJob(job.status)}`} key={job.jobId}>
                <td><StatusBadge tone={statusToneForJob(job.status)} /></td>
                <td><time className="timestamp" dateTime={job.startedAt}>{formatKstTime(job.startedAt, i18n.language)}</time></td>
                <td>{t(`mode.${job.mode}`)}</td>
                <td className="num">{job.filesDone}/{job.filesTotal}</td>
                <td className="num">{formatCount(job.rowsSent, i18n.language)}</td>
                <td className={job.failureCount > 0 ? "num num--danger" : "num"}>{job.failureCount}</td>
                <td className="truncate">{job.latestMessage}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
