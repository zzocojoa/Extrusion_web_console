import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import test, { after } from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";
import ts from "typescript";

const testDirectory = path.dirname(fileURLToPath(import.meta.url));
const sourcePath = path.resolve(testDirectory, "../src/appRouting.ts");
const temporaryDirectory = await mkdtemp(path.join(tmpdir(), "ewc-app-routing-"));
const outputPath = path.join(temporaryDirectory, "appRouting.mjs");
const source = await readFile(sourcePath, "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ES2022,
    target: ts.ScriptTarget.ES2022,
  },
  fileName: sourcePath,
});
await writeFile(outputPath, compiled.outputText, "utf8");

const { pageFromPathname, pathnameForPage } = await import(pathToFileURL(outputPath).href);

after(async () => {
  await rm(temporaryDirectory, { force: true, recursive: true });
});

test("maps supported deep links to the initial application page", () => {
  assert.equal(pageFromPathname("/"), "dashboard");
  assert.equal(pageFromPathname("/upload"), "upload");
  assert.equal(pageFromPathname("/upload/"), "upload");
  assert.equal(pageFromPathname("/logs"), "logs");
  assert.equal(pageFromPathname("/settings"), "settings");
});

test("falls back to Dashboard for unsupported paths", () => {
  assert.equal(pageFromPathname("/unknown"), "dashboard");
  assert.equal(pageFromPathname("/upload/nested"), "dashboard");
});

test("maps every application page to its canonical path", () => {
  assert.equal(pathnameForPage("dashboard"), "/");
  assert.equal(pathnameForPage("upload"), "/upload");
  assert.equal(pathnameForPage("logs"), "/logs");
  assert.equal(pathnameForPage("settings"), "/settings");
});
