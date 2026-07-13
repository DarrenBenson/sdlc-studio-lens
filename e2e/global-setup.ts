import { execSync } from "node:child_process";
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
  // DO NOT unlink the database file here.
  //
  // Playwright starts the `webServer` processes BEFORE this runs, and the backend now
  // touches the database during startup (it clears any project left stuck in "syncing"
  // by a hard stop - BG-01KXDFGD). So by the time we get here the server has already
  // opened this SQLite file and is holding a pooled connection to it.
  //
  // Deleting the file out from under it leaves the server bound to a deleted inode: the
  // tables we then create with Alembic land in a NEW file the server never sees, and
  // every query fails with "no such table: projects". You cannot unlink a file a running
  // process is holding open and expect it to notice.
  //
  // Migrating in place is enough. `alembic upgrade head` is idempotent, and
  // global-teardown removes the file once the servers are down, so each run still starts
  // from a clean database.
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

  // A crashed previous run can leave the fixture behind (the teardown removes the DB, but
  // only if it got to run). Clear it first so setup is idempotent rather than fragile.
  await fetch(`${API_BASE}/projects/e2e-test-project`, { method: "DELETE" }).catch(
    () => undefined,
  );

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
