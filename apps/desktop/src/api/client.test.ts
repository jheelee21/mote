import { describe, expect, it } from "vitest";

import { buildUrl } from "./client";

describe("buildUrl", () => {
  it("joins base and path with exactly one slash", () => {
    expect(buildUrl("http://127.0.0.1:8765", "/health")).toBe("http://127.0.0.1:8765/health");
    expect(buildUrl("http://127.0.0.1:8765/", "health")).toBe("http://127.0.0.1:8765/health");
    expect(buildUrl("http://127.0.0.1:8765//", "//jobs/1")).toBe("http://127.0.0.1:8765/jobs/1");
  });
});
