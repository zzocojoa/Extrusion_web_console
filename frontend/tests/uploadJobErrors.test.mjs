import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import test, { after } from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";
import ts from "typescript";

const testDirectory = path.dirname(fileURLToPath(import.meta.url));
const sourcePath = path.resolve(testDirectory, "../src/api/uploadJobErrors.ts");
const temporaryDirectory = await mkdtemp(path.join(tmpdir(), "ewc-upload-job-errors-"));
const compiledPath = path.join(temporaryDirectory, "uploadJobErrors.mjs");
const source = await readFile(sourcePath, "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ES2022,
    target: ts.ScriptTarget.ES2022,
  },
  fileName: sourcePath,
});
await writeFile(compiledPath, compiled.outputText, "utf8");
const {
  parseUploadWorkerUnavailableError,
  UPLOAD_WORKER_RESTART_RECOVERY,
  UPLOAD_WORKER_RETRY_RECOVERY,
} = await import(pathToFileURL(compiledPath).href);

after(async () => {
  await rm(temporaryDirectory, { force: true, recursive: true });
});

const jobId = "upl_abc123def456";
const response = () => new Response(null, {
  status: 503,
  headers: { Location: `/api/upload/jobs/${jobId}` },
});

test("requires restart for a reconciled worker submission failure", () => {
  const error = parseUploadWorkerUnavailableError(response(), {
    reason: "upload_worker_unavailable",
    jobId,
    restartRequired: true,
    recovery: UPLOAD_WORKER_RETRY_RECOVERY,
  });

  assert.equal(error?.jobId, jobId);
  assert.equal(error?.restartRequired, true);
  assert.equal(error?.recovery, UPLOAD_WORKER_RETRY_RECOVERY);
});

test("preserves the launcher restart instruction for reconciliation failure", () => {
  const error = parseUploadWorkerUnavailableError(response(), {
    reason: "upload_worker_reconciliation_failed",
    jobId,
    restartRequired: true,
    recovery: UPLOAD_WORKER_RESTART_RECOVERY,
  });

  assert.equal(error?.jobId, jobId);
  assert.equal(error?.restartRequired, true);
  assert.equal(error?.message, UPLOAD_WORKER_RESTART_RECOVERY);
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
