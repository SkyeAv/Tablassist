import { describe, expect, it } from "bun:test";

import { createTablassistCache } from "./cache.ts";

describe("createTablassistCache", () => {
  it("caches successful lookups", async () => {
    let calls = 0;
    const cache = createTablassistCache(async (command) => {
      calls += 1;
      return `value:${command}`;
    });

    const first = await cache.get("sectionSchema");
    const second = await cache.get("sectionSchema");

    expect(first).toBe("value:section-schema");
    expect(second).toBe("value:section-schema");
    expect(calls).toBe(1);
  });

  it("does not cache failures", async () => {
    let calls = 0;
    const cache = createTablassistCache(async () => {
      calls += 1;
      throw new Error("boom");
    });

    await expect(cache.get("sectionSchema")).rejects.toThrow("boom");
    await expect(cache.get("sectionSchema")).rejects.toThrow("boom");

    expect(calls).toBe(2);
  });
});
