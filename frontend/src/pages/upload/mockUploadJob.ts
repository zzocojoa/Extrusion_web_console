import type {
  JobEvent,
  UploadJobDetail,
  UploadJobFile,
  UploadJobStatus,
} from "../../api/uploadJobs";

export function getMockUploadJob(
  jobId: string,
  startedAtMs: number,
  paused: boolean,
  cancelled: boolean,
): UploadJobDetail {
  const elapsed = Math.max(0, Date.now() - startedAtMs);
  const step = paused ? 35 : Math.min(100, Math.floor(elapsed / 70));
  const status: UploadJobStatus = cancelled
    ? "cancelled"
    : paused
      ? "paused"
      : step >= 100
        ? "partial_failed"
        : "running";
  const firstProcessed = Math.min(16000, Math.floor(16000 * Math.min(step, 100) / 100));
  const secondProcessed = status === "partial_failed" ? 1400 : Math.min(6400, Math.max(0, Math.floor((step - 45) * 160)));
  const files: UploadJobFile[] = [
    {
      jobFileId: 1,
      jobId,
      previewItemId: 101,
      fileKey: "mock-target-1",
      folderLabel: "PLC",
      folderPath: "demo://upload-job",
      filename: "integrated_plc_upload_sample_A.csv",
      path: "demo://upload-job/integrated_plc_upload_sample_A.csv",
      kind: "plc",
      fileDate: "2026-06-02",
      fileSignature: "size=15000|mtime_ns=1",
      status: step >= 65 ? "succeeded" : status === "cancelled" ? "cancelled" : "running",
      rowCount: 16000,
      processedRows: status === "cancelled" ? firstProcessed : firstProcessed,
      uploadedRows: Math.min(firstProcessed, 16000),
      acceptedRows: Math.max(0, Math.min(firstProcessed - 18, 15982)),
      insertedRows: Math.max(0, Math.min(firstProcessed - 18, 15982)),
      resumeOffset: step >= 65 ? 0 : firstProcessed,
      retryCount: 0,
      startedAt: new Date(startedAtMs).toISOString(),
      finishedAt: step >= 65 ? new Date(startedAtMs + 4600).toISOString() : null,
      lastErrorCode: null,
      lastErrorMessage: null,
    },
    {
      jobFileId: 2,
      jobId,
      previewItemId: 102,
      fileKey: "mock-target-2",
      folderLabel: "PLC",
      folderPath: "demo://upload-job",
      filename: "260602_plc_line_2.csv",
      path: "demo://upload-job/260602_plc_line_2.csv",
      kind: "plc",
      fileDate: "2026-06-02",
      fileSignature: "size=6400|mtime_ns=2",
      status: status === "partial_failed" ? "failed" : status === "cancelled" ? "cancelled" : step < 65 ? "queued" : "running",
      rowCount: 6400,
      processedRows: secondProcessed,
      uploadedRows: secondProcessed,
      acceptedRows: Math.max(0, secondProcessed - 4),
      insertedRows: Math.max(0, secondProcessed - 4),
      resumeOffset: status === "partial_failed" ? 1400 : secondProcessed,
      retryCount: 0,
      startedAt: step >= 65 ? new Date(startedAtMs + 4700).toISOString() : null,
      finishedAt: status === "partial_failed" || status === "cancelled" ? new Date().toISOString() : null,
      lastErrorCode: status === "partial_failed" ? "upload_failed" : null,
      lastErrorMessage: status === "partial_failed" ? "Edge upload timed out after retry attempts." : null,
    },
  ];
  const processedRows = files.reduce((sum, file) => sum + file.processedRows, 0);
  const uploadedRows = files.reduce((sum, file) => sum + file.uploadedRows, 0);
  const acceptedRows = files.reduce((sum, file) => sum + file.acceptedRows, 0);
  const events: JobEvent[] = buildEvents(jobId, startedAtMs, status, step);
  return {
    job: {
      jobId,
      previewRunId: "mock_preview",
      retryOfJobId: null,
      mode: "preview_targets",
      status,
      requestedAt: new Date(startedAtMs).toISOString(),
      startedAt: new Date(startedAtMs + 250).toISOString(),
      finishedAt: ["partial_failed", "cancelled"].includes(status) ? new Date().toISOString() : null,
      actor: "local_operator",
      summary: {
        totalFiles: 2,
        succeededFiles: files.filter((file) => file.status === "succeeded").length,
        failedFiles: files.filter((file) => file.status === "failed").length,
        cancelledFiles: files.filter((file) => file.status === "cancelled").length,
        totalRows: 22400,
        processedRows,
        uploadedRows,
        acceptedRows,
        insertedRows: acceptedRows,
        warningCount: status === "partial_failed" ? 1 : 0,
      },
      errorCode: status === "partial_failed" ? "upload_failed" : null,
      errorMessage: status === "partial_failed" ? "One target file failed and can be retried." : null,
    },
    files,
    events,
    eventCursor: { latestSeq: events.length > 0 ? events[events.length - 1].seq : 0 },
  };
}

function buildEvents(jobId: string, startedAtMs: number, status: UploadJobStatus, step: number): JobEvent[] {
  const base = new Date(startedAtMs).toISOString();
  const events: JobEvent[] = [
    event(1, jobId, base, "info", "job.created", "Upload job was queued from preview targets."),
    event(2, jobId, new Date(startedAtMs + 250).toISOString(), "info", "job.started", "Upload job started."),
    event(3, jobId, new Date(startedAtMs + 500).toISOString(), "info", "file.started", "Started integrated_plc_upload_sample_A.csv.", 1),
  ];
  if (step > 25) events.push(event(4, jobId, new Date(startedAtMs + 1600).toISOString(), "debug", "file.progress", "Progress 5200/16000.", 1));
  if (step > 65) events.push(event(5, jobId, new Date(startedAtMs + 4600).toISOString(), "info", "file.succeeded", "Completed integrated_plc_upload_sample_A.csv.", 1));
  if (status === "partial_failed") {
    events.push(event(6, jobId, new Date(startedAtMs + 5100).toISOString(), "info", "file.started", "Started 260602_plc_line_2.csv.", 2));
    events.push(event(7, jobId, new Date(startedAtMs + 6500).toISOString(), "error", "file.failed", "Failed 260602_plc_line_2.csv: Edge upload timed out after retry attempts.", 2));
    events.push(event(8, jobId, new Date(startedAtMs + 6700).toISOString(), "warning", "job.partial_failed", "Upload job finished with status partial_failed."));
  }
  if (status === "paused") events.push(event(6, jobId, new Date().toISOString(), "warning", "job.paused", "Upload job paused."));
  if (status === "cancelled") events.push(event(6, jobId, new Date().toISOString(), "warning", "job.cancelled", "Upload job finished with status cancelled."));
  return events;
}

function event(
  seq: number,
  jobId: string,
  ts: string,
  level: JobEvent["level"],
  eventType: string,
  message: string,
  jobFileId: number | null = null,
): JobEvent {
  return {
    eventId: seq,
    jobId,
    seq,
    ts,
    level,
    eventType,
    message,
    jobFileId,
    data: {},
  };
}
