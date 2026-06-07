import { spawn } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";

const mode = process.argv[2] ?? "mock";
const allowedModes = new Set(["mock", "api"]);

if (!allowedModes.has(mode)) {
  console.error(`Unsupported frontend build mode: ${mode}`);
  process.exit(1);
}

const env = { ...process.env };
if (mode === "api") {
  env.VITE_API_MODE = "api";
} else {
  delete env.VITE_API_MODE;
}

function run(command, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      env,
      shell: true,
      stdio: "inherit",
    });
    child.on("error", reject);
    child.on("exit", (code) => {
      if (code === 0) {
        resolve();
        return;
      }
      reject(new Error(`${command} ${args.join(" ")} exited with ${code}`));
    });
  });
}

await run("tsc", ["--noEmit"]);
await run("vite", ["build"]);

const distDir = join(process.cwd(), "dist");
await mkdir(distDir, { recursive: true });
await writeFile(
  join(distDir, "frontend-build-info.json"),
  JSON.stringify(
    {
      schemaVersion: 1,
      frontendMode: mode,
      createdUtc: new Date().toISOString(),
    },
    null,
    2,
  ) + "\n",
  "utf8",
);

console.log(`frontend build mode: ${mode}`);
