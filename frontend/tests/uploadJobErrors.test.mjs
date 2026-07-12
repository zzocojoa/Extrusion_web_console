import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import test, { after } from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";
import ts from "typescript";

const testDirectory = path.dirname(fileURLToPath(import.meta.url));
const apiDirectory = path.resolve(testDirectory, "../src/api");
const temporaryDirectory = await mkdtemp(path.join(tmpdir(), "ewc-upload-job-errors-"));
const compilerOptions = {
  module: ts.ModuleKind.ES2022,
  target: ts.ScriptTarget.ES2022,
};

async function compileModule(sourceName, outputName, transform = (source) => source) {
  const sourcePath = path.join(apiDirectory, sourceName);
  const source = transform(await readFile(sourcePath, "utf8"));
  const compiled = ts.transpileModule(source, { compilerOptions, fileName: sourcePath });
  await writeFile(path.join(temporaryDirectory, outputName), compiled.outputText, "utf8");
}

await compileModule("uploadJobErrors.ts", "uploadJobErrors.mjs");
await compileModule("client.ts", "client.mjs");
await compileModule("uploadJobs.ts", "uploadJobs.mjs", (source) => source
  .replaceAll('"./client"', '"./client.mjs"')
  .replaceAll('"./uploadJobErrors"', '"./uploadJobErrors.mjs"'));

const {
  parseUploadWorkerUnavailableError,
  shouldClearRecoveredWorkerFailure,
  uploadWorkerRecoveryTranslationKey,
  UPLOAD_WORKER_RESTART_RECOVERY,
  UPLOAD_WORKER_RETRY_RECOVERY,
} = await import(pathToFileURL(path.join(temporaryDirectory, "uploadJobErrors.mjs")).href);
const {
  controlUploadJob,
  createUploadJob,
  fetchLatestUploadJob,
  fetchUploadJob,
  retryUploadJob,
} = await import(pathToFileURL(path.join(temporaryDirectory, "uploadJobs.mjs")).href);

const originalFetch = globalThis.fetch;
const originalWindow = globalThis.window;
globalThis.window = {
  __EWC_BOOTSTRAP__: {},
  location: { origin: "http://127.0.0.1:8000" },
  localStorage: { getItem: () => "ko" },
};

after(async () => {
  globalThis.fetch = originalFetch;
  if (originalWindow === undefined) delete globalThis.window;
  else globalThis.window = originalWindow;
  await rm(temporaryDirectory, { force: true, recursive: true });
});

const jobId = "upl_abc123def456";
const response = () => new Response(null, {
  status: 503,
  headers: { Location: `/api/upload/jobs/${jobId}` },
});

function reconciliationFailureResponse() {
  return new Response(JSON.stringify({
    detail: {
      reason: "upload_worker_reconciliation_failed",
      jobId,
      restartRequired: true,
      recovery: UPLOAD_WORKER_RESTART_RECOVERY,
    },
  }), {
    status: 503,
    headers: {
      "Content-Type": "application/json",
      Location: `/api/upload/jobs/${jobId}`,
    },
  });
}

async function assertReconciliationFailure(request) {
  globalThis.fetch = async () => reconciliationFailureResponse();
  await assert.rejects(request(), (error) => {
    assert.equal(error?.name, "UploadWorkerUnavailableError");
    assert.equal(error?.jobId, jobId);
    assert.equal(error?.reason, "upload_worker_reconciliation_failed");
    assert.equal(error?.restartRequired, true);
    return true;
  });
}

test("requires restart for a reconciled worker submission failure", () => {
  const error = parseUploadWorkerUnavailableError(response(), {
    reason: "upload_worker_unavailable",
    jobId,
    restartRequired: true,
    recovery: UPLOAD_WORKER_RETRY_RECOVERY,
  });

  assert.equal(error?.jobId, jobId);
  assert.equal(error?.reason, "upload_worker_unavailable");
  assert.equal(error?.restartRequired, true);
  assert.equal(error?.recovery, UPLOAD_WORKER_RETRY_RECOVERY);
  assert.equal(uploadWorkerRecoveryTranslationKey(error), "upload.job.workerUnavailableRecovery");
});

test("preserves the launcher restart instruction for reconciliation failure", () => {
  const error = parseUploadWorkerUnavailableError(response(), {
    reason: "upload_worker_reconciliation_failed",
    jobId,
    restartRequired: true,
    recovery: UPLOAD_WORKER_RESTART_RECOVERY,
  });

  assert.equal(error?.jobId, jobId);
  assert.equal(error?.reason, "upload_worker_reconciliation_failed");
  assert.equal(error?.restartRequired, true);
  assert.equal(error?.message, UPLOAD_WORKER_RESTART_RECOVERY);
  assert.equal(
    uploadWorkerRecoveryTranslationKey(error),
    "upload.job.workerReconciliationFailedRecovery",
  );
});

test("rejects mismatched body and Location job IDs", () => {
  const error = parseUploadWorkerUnavailableError(response(), {
    reason: "upload_worker_unavailable",
    jobId: "upl_000000000000",
    restartRequired: false,
    recovery: UPLOAD_WORKER_RETRY_RECOVERY,
  });

  assert.equal(error, null);
});

test("rejects inconsistent restart flags and recovery text", () => {
  assert.equal(parseUploadWorkerUnavailableError(response(), {
    reason: "upload_worker_reconciliation_failed",
    jobId,
    restartRequired: false,
    recovery: UPLOAD_WORKER_RESTART_RECOVERY,
  }), null);
  assert.equal(parseUploadWorkerUnavailableError(response(), {
    reason: "upload_worker_reconciliation_failed",
    jobId,
    restartRequired: true,
    recovery: "untrusted recovery text",
  }), null);
});

test("public upload-job requests preserve structured worker recovery failures", async () => {
  await assertReconciliationFailure(() => createUploadJob("prv_done", {
    expectedTargetRows: 2,
    expectedTargetFiles: 1,
  }));
  await assertReconciliationFailure(() => retryUploadJob("upl_000000000001", {
    expectedRemainingRows: 2,
    expectedRetryFiles: 1,
  }));
  await assertReconciliationFailure(() => fetchLatestUploadJob());
  await assertReconciliationFailure(() => fetchUploadJob(jobId));
  await assertReconciliationFailure(() => controlUploadJob(jobId, "pause"));
});

test("worker recovery translation keys resolve to local Korean and English copy", async () => {
  const error = parseUploadWorkerUnavailableError(response(), {
    reason: "upload_worker_reconciliation_failed",
    jobId,
    restartRequired: true,
    recovery: UPLOAD_WORKER_RESTART_RECOVERY,
  });
  const key = uploadWorkerRecoveryTranslationKey(error);
  const [english, korean] = await Promise.all([
    readFile(path.resolve(testDirectory, "../src/i18n/locales/en.json"), "utf8").then(JSON.parse),
    readFile(path.resolve(testDirectory, "../src/i18n/locales/ko.json"), "utf8").then(JSON.parse),
  ]);
  const leaf = key.slice("upload.job.".length);

  assert.equal(english.upload.job[leaf], UPLOAD_WORKER_RESTART_RECOVERY);
  assert.equal(
    korean.upload.job[leaf],
    "업로드 작업을 시작하거나 재시도하기 전에 웹 콘솔을 런처에서 다시 시작하세요.",
  );
  assert.notEqual(korean.upload.job[leaf], UPLOAD_WORKER_RESTART_RECOVERY);
});

test("only a matching terminal reconciliation failure clears after startup recovery", () => {
  const reconciliationError = parseUploadWorkerUnavailableError(response(), {
    reason: "upload_worker_reconciliation_failed",
    jobId,
    restartRequired: true,
    recovery: UPLOAD_WORKER_RESTART_RECOVERY,
  });
  const submissionError = parseUploadWorkerUnavailableError(response(), {
    reason: "upload_worker_unavailable",
    jobId,
    restartRequired: true,
    recovery: UPLOAD_WORKER_RETRY_RECOVERY,
  });

  assert.equal(shouldClearRecoveredWorkerFailure(reconciliationError, jobId, true), true);
  assert.equal(shouldClearRecoveredWorkerFailure(reconciliationError, jobId, false), false);
  assert.equal(shouldClearRecoveredWorkerFailure(reconciliationError, "upl_000000000000", true), false);
  assert.equal(shouldClearRecoveredWorkerFailure(submissionError, jobId, true), false);
});
