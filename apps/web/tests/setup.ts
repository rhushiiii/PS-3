import { spawn } from "node:child_process";
import { resolve } from "node:path";
import process from "node:process";
import { createInterface } from "node:readline";

export const WEB_URL = "http://127.0.0.1:3105";
export const API_URL = "http://127.0.0.1:8105/api/v1";

export default async function setup() {
  const python = resolve(
    process.cwd(),
    "../../services/api/.venv",
    process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
  );
  const child = spawn(
    python,
    ["scripts/test-stack.py", "--api-port", "8105", "--web-port", "3105"],
    {
      cwd: process.cwd(),
      stdio: ["pipe", "pipe", "pipe"],
    },
  );
  const lines = createInterface({ input: child.stdout });
  let diagnostics = "";
  child.stderr.on("data", (value: Buffer) => {
    diagnostics += value.toString();
  });
  const exited = new Promise<void>((resolveExit) =>
    child.once("exit", () => resolveExit()),
  );
  try {
    await new Promise<void>((resolveReady, reject) => {
      const timer = setTimeout(
        () => reject(new Error("Test stack startup timed out")),
        140_000,
      );
      child.once("error", () => {
        clearTimeout(timer);
        reject(new Error("Unable to launch isolated test stack"));
      });
      child.once("exit", (code) => {
        clearTimeout(timer);
        reject(
          new Error(`Isolated test stack exited (${code}). ${diagnostics}`),
        );
      });
      lines.on("line", (line) => {
        if (line === '{"ready": true}') {
          clearTimeout(timer);
          resolveReady();
        }
      });
    });
  } catch (error) {
    child.stdin.end();
    await exited;
    throw error;
  }
  return async () => {
    child.stdin.end();
    await exited;
    lines.close();
    if (child.exitCode !== 0)
      throw new Error(
        "Test stack cleanup failed. Inspect its local database/process state.",
      );
  };
}
