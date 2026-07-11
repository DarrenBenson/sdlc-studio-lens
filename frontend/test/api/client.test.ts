import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchAggregateStats, fetchProjects } from "../../src/api/client.ts";

/**
 * CR-01KX8B83: the list/aggregate GET helpers must surface the canonical
 * `{ error: { message } }` body via extractErrorMessage, not a bare status string.
 */

function mockFetchOnce(body: unknown, ok = false, status = 500): void {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok,
      status,
      json: async () => body,
    } as Response),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("client error handling", () => {
  it("fetchProjects surfaces the canonical error message", async () => {
    mockFetchOnce({ error: { code: "INTERNAL", message: "database exploded" } });
    await expect(fetchProjects()).rejects.toThrow("database exploded");
  });

  it("fetchAggregateStats surfaces the canonical error message", async () => {
    mockFetchOnce({ error: { code: "INTERNAL", message: "stats unavailable" } });
    await expect(fetchAggregateStats()).rejects.toThrow("stats unavailable");
  });

  it("falls back to a status message when the body is not JSON", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        json: async () => {
          throw new Error("not json");
        },
      } as Response),
    );
    await expect(fetchProjects()).rejects.toThrow("Request failed (503)");
  });
});
