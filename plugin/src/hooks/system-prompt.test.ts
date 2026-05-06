import { describe, expect, it } from "bun:test"
import type { Model } from "@opencode-ai/sdk"

import { createAgentTracker } from "../agent-tracker.ts"
import type { TablassistCache } from "../cache.ts"
import { createSystemPromptHook, formatSystemPromptResources } from "./system-prompt.ts"

const MOCK_RESOURCES = {
  sectionSchema: "schema",
  docsTableConfig: "table docs",
}

function mockCache(): TablassistCache {
  return {
    get: async (key) => MOCK_RESOURCES[key],
    getSystemPromptResources: async () => MOCK_RESOURCES,
  }
}

const STUB_MODEL = {} as Model

describe("formatSystemPromptResources", () => {
  it("formats selected cached resources with headers", () => {
    const parts = formatSystemPromptResources(MOCK_RESOURCES, ["sectionSchema", "docsTableConfig"])

    expect(parts).toHaveLength(2)
    expect(parts[0]).toContain("## Tablassert Section JSON Schema")
    expect(parts[1]).toContain("## Table Configuration Documentation")
  })
})

describe("createSystemPromptHook conditional injection", () => {
  it("injects the full bundle for the-builder", async () => {
    const tracker = createAgentTracker()
    tracker.track("sess-1", "the-builder")
    const hook = createSystemPromptHook(mockCache(), tracker)
    const output = { system: [] as string[] }

    await hook({ sessionID: "sess-1", model: STUB_MODEL }, output)

    expect(output.system).toHaveLength(2)
    expect(output.system[0]).toContain("Schema")
  })

  it("injects a smaller bundle for the-configurator", async () => {
    const tracker = createAgentTracker()
    tracker.track("sess-1", "the-configurator")
    const hook = createSystemPromptHook(mockCache(), tracker)
    const output = { system: [] as string[] }

    await hook({ sessionID: "sess-1", model: STUB_MODEL }, output)

    expect(output.system).toHaveLength(2)
  })

  it("injects only the orchestration bundle for the-pioneer", async () => {
    const tracker = createAgentTracker()
    tracker.track("sess-1", "the-pioneer")
    const hook = createSystemPromptHook(mockCache(), tracker)
    const output = { system: [] as string[] }

    await hook({ sessionID: "sess-1", model: STUB_MODEL }, output)

    expect(output.system).toHaveLength(1)
    expect(output.system[0]).toContain("## Table Configuration Documentation")
  })

  it("injects nothing for the-extractor", async () => {
    const tracker = createAgentTracker()
    tracker.track("sess-1", "the-extractor")
    const hook = createSystemPromptHook(mockCache(), tracker)
    const output = { system: [] as string[] }

    await hook({ sessionID: "sess-1", model: STUB_MODEL }, output)

    expect(output.system).toHaveLength(0)
  })

  it("injects nothing for non-tablassist agents", async () => {
    const tracker = createAgentTracker()
    tracker.track("sess-1", "build")
    const hook = createSystemPromptHook(mockCache(), tracker)
    const output = { system: [] as string[] }

    await hook({ sessionID: "sess-1", model: STUB_MODEL }, output)

    expect(output.system).toHaveLength(0)
  })

  it("falls back to configurator resources when sessionID is undefined", async () => {
    const tracker = createAgentTracker()
    const hook = createSystemPromptHook(mockCache(), tracker)
    const output = { system: [] as string[] }

    await hook({ sessionID: undefined, model: STUB_MODEL }, output)

    expect(output.system).toHaveLength(2)
  })

  it("falls back to configurator resources for untracked session", async () => {
    const tracker = createAgentTracker()
    const hook = createSystemPromptHook(mockCache(), tracker)
    const output = { system: [] as string[] }

    await hook({ sessionID: "unknown-sess", model: STUB_MODEL }, output)

    expect(output.system).toHaveLength(2)
  })
})
