import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import test, { after } from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";
import ts from "typescript";

const testDirectory = path.dirname(fileURLToPath(import.meta.url));
const apiDirectory = path.resolve(testDirectory, "../src/api");
const temporaryDirectory = await mkdtemp(path.join(tmpdir(), "ewc-upload-preview-errors-"));
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

await compileModule("client.ts", "client.mjs");
await compileModule("uploadPreview.ts", "uploadPreview.mjs", (source) =>
  source.replaceAll('"./client"', '"./client.mjs"'),
);

const {
  createUploadPreview,
  parsePreviewWorkerUnavailableError,
  previewWorkerRecoveryTranslationKey,
  PREVIEW_WORKER_RESTART_RECOVERY,
  PREVIEW_WORKER_RETRY_RECOVERY,
} = await import(pathToFileURL(path.join(temporaryDirectory, "uploadPreview.mjs")).href);

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

const previewRunId = "prv_abc123def456";

function workerFailureResponse(reason, recovery) {
  return new Response(JSON.stringify({
    detail: {
      reason,
      previewRunId,
      restartRequired: true,
      recovery,
    },
  }), {
    status: 503,
    headers: {
      "Content-Type": "application/json",
      Location: `/api/upload/preview/${previewRunId}`,
    },
  });
}

test("preserves the two trusted Preview worker recovery contracts", () => {
  const submissionError = parsePreviewWorkerUnavailableError(
    workerFailureResponse("preview_worker_unavailable", PREVIEW_WORKER_RETRY_RECOVERY),
    {
      reason: "preview_worker_unavailable",
      previewRunId,
      restartRequired: true,
      recovery: PREVIEW_WORKER_RETRY_RECOVERY,
    },
  );
  const reconciliationError = parsePreviewWorkerUnavailableError(
    workerFailureResponse("preview_worker_reconciliation_failed", PREVIEW_WORKER_RESTART_RECOVERY),
    {
      reason: "preview_worker_reconciliation_failed",
      previewRunId,
      restartRequired: true,
      recovery: PREVIEW_WORKER_RESTART_RECOVERY,
    },
  );

  assert.equal(submissionError?.name, "PreviewWorkerUnavailableError");
  assert.equal(submissionError?.previewRunId, previewRunId);
  assert.equal(
    previewWorkerRecoveryTranslationKey(submissionError),
    "upload.preview.workerUnavailableRecovery",
  );
  assert.equal(
    previewWorkerRecoveryTranslationKey(reconciliationError),
    "upload.preview.workerReconciliationFailedRecovery",
  );
});

test("rejects forged or inconsistent Preview worker recovery payloads", () => {
  const response = workerFailureResponse("preview_worker_unavailable", PREVIEW_WORKER_RETRY_RECOVERY);
  assert.equal(parsePreviewWorkerUnavailableError(response, {
    reason: "preview_worker_unavailable",
    previewRunId: "prv_000000000000",
    restartRequired: true,
    recovery: PREVIEW_WORKER_RETRY_RECOVERY,
  }), null);
  assert.equal(parsePreviewWorkerUnavailableError(response, {
    reason: "preview_worker_unavailable",
    previewRunId,
    restartRequired: false,
    recovery: "untrusted recovery text",
  }), null);
});

test("createUploadPreview surfaces the structured Preview worker failure", async () => {
  globalThis.fetch = async () => workerFailureResponse(
    "preview_worker_reconciliation_failed",
    PREVIEW_WORKER_RESTART_RECOVERY,
  );

  await assert.rejects(
    createUploadPreview({}),
    (error) => {
      assert.equal(error?.name, "PreviewWorkerUnavailableError");
      assert.equal(error?.previewRunId, previewRunId);
      assert.equal(error?.message, PREVIEW_WORKER_RESTART_RECOVERY);
      return true;
    },
  );
});

test("Preview worker recovery translation keys resolve to Korean and English copy", async () => {
  const response = workerFailureResponse("preview_worker_unavailable", PREVIEW_WORKER_RETRY_RECOVERY);
  const error = parsePreviewWorkerUnavailableError(response, {
    reason: "preview_worker_unavailable",
    previewRunId,
    restartRequired: true,
    recovery: PREVIEW_WORKER_RETRY_RECOVERY,
  });
  const key = previewWorkerRecoveryTranslationKey(error);
  const [english, korean] = await Promise.all([
    readFile(path.resolve(testDirectory, "../src/i18n/locales/en.json"), "utf8").then(JSON.parse),
    readFile(path.resolve(testDirectory, "../src/i18n/locales/ko.json"), "utf8").then(JSON.parse),
  ]);
  const leaf = key.slice("upload.preview.".length);

  assert.equal(english.upload.preview[leaf], PREVIEW_WORKER_RETRY_RECOVERY);
  assert.equal(
    korean.upload.preview[leaf],
    "웹 콘솔을 런처에서 다시 시작하고 저장된 실패 미리보기를 확인한 다음, 미리보기를 다시 실행하세요.",
  );
});
