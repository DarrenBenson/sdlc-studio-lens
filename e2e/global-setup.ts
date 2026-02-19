import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const BACKEND_DIR = path.resolve(__dirname, "../backend");
const DB_PATH = "/tmp/sdlc-lens-e2e.db";
const DB_URL = `sqlite+aiosqlite:///${DB_PATH}`;
const API_BASE = "http://localhost:8000/api/v1";
const FIXTURES_DIR = path.resolve(__dirname, "fixtures/sdlc-docs");

async function waitForServer(
  url: string,
  timeoutMs: number = 30_000,
): Promise<void> {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(url);
      if (res.ok) return;
    } catch {
      // Server not ready yet
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error(`Server at ${url} did not start within ${timeoutMs}ms`);
}

async function pollSyncComplete(
  slug: string,
  timeoutMs: number = 30_000,
): Promise<void> {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const res = await fetch(`${API_BASE}/projects/${slug}`);
    if (res.ok) {
      const project = (await res.json()) as { sync_status: string };
      if (project.sync_status === "synced") return;
      if (project.sync_status === "error") {
        throw new Error("Sync failed with error status");
      }
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error(`Sync did not complete within ${timeoutMs}ms`);
}

export default async function globalSetup(): Promise<void> {
  // Remove stale DB if it exists
  if (fs.existsSync(DB_PATH)) {
    fs.unlinkSync(DB_PATH);
  }
  if (fs.existsSync(`${DB_PATH}-journal`)) {
    fs.unlinkSync(`${DB_PATH}-journal`);
  }

  // Run Alembic migrations
  execSync("alembic upgrade head", {
    cwd: BACKEND_DIR,
    env: {
      ...process.env,
      PYTHONPATH: path.join(BACKEND_DIR, "src"),
      SDLC_LENS_DATABASE_URL: DB_URL,
    },
    stdio: "pipe",
  });

  // Wait for backend to be ready
  await waitForServer(`${API_BASE}/system/health`);

  // Create fixture project
  const createRes = await fetch(`${API_BASE}/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: "E2E Test Project",
      sdlc_path: FIXTURES_DIR,
    }),
  });

  if (!createRes.ok) {
    const body = await createRes.text();
    throw new Error(`Failed to create fixture project: ${createRes.status} ${body}`);
  }

  // Trigger sync
  const syncRes = await fetch(`${API_BASE}/projects/e2e-test-project/sync`, {
    method: "POST",
  });

  if (!syncRes.ok) {
    const body = await syncRes.text();
    throw new Error(`Failed to trigger sync: ${syncRes.status} ${body}`);
  }

  // Wait for sync to complete
  await pollSyncComplete("e2e-test-project");
}
