import fs from "node:fs";

const DB_PATH = "/tmp/sdlc-lens-e2e.db";

export default async function globalTeardown(): Promise<void> {
  for (const file of [DB_PATH, `${DB_PATH}-journal`]) {
    if (fs.existsSync(file)) {
      fs.unlinkSync(file);
    }
  }
}
