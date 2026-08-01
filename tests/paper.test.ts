import { describe, expect, it } from "vitest";
import { checkPaperReachable } from "../src/bot/paper.js";

describe("checkPaperReachable", () => {
  it("reports an unreachable Paper endpoint as an external failure", async () => {
    const result = await checkPaperReachable("127.0.0.1", 1, 250);

    expect(result.reachable).toBe(false);
    expect(result.error).toContain("Paper server is not reachable");
  });
});
