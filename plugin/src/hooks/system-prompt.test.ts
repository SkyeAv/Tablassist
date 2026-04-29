import { describe, expect, it } from "bun:test"
import type { Model } from "@opencode-ai/sdk"

import { createAgentTracker } from "../agent-tracker.ts"
import type { TablassistCache } from "../cache.ts"
import { createSystemPromptHook, formatSystemPromptResources } from "./system-prompt.ts"

const MOCK_RESOURCES = {
  sectionSchema: "schema",
  docsTableConfig: "table docs",
  docsAdvancedExamples: "advanced",
  docsTutorial: "tutorial",
  exampleNoSections: "no sections",
  exampleWithSections: "with sections",
}

function mockCache(): TablassistCache {
  return {
    get: async (key) => MOCK_RESOURCES[key],
    getSystemPromptResources: async () => MOCK_RESOURCES,
  }
}

const STUB_MODEL = {} as Model

describe("formatSystemPromptResources", () => {
  it("formats all cached resources with headers", () => {
    const parts = formatSystemPromptResources(MOCK_RESOURCES)

    expect(parts).toHaveLength(6)
    expect(parts[0]).toContain("## Tablassert Section JSON Schema")
    expect(parts[3]).toContain("## Tutorial Reference")
    expect(parts[5]).toContain("with sections")
  })
})

describe("createSystemPromptHook conditional injection", () => {
  it("injects all resources for the-builder", async () => {
    const tracker = createAgentTracker()
    tracker.track("sess-1", "the-builder")
    const hook = createSystemPromptHook(mockCache(), tracker)
    const output = { system: [] as string[] }

    await hook({ sessionID: "sess-1", model: STUB_MODEL }, output)

    expect(output.system).toHaveLength(6)
    expect(output.system[0]).toContain("Schema")
  })

  it("injects all resources for the-configurator", async () => {
    const tracker = createAgentTracker()
    tracker.track("sess-1", "the-configurator")
    const hook = createSystemPromptHook(mockCache(), tracker)
    const output = { system: [] as string[] }

    await hook({ sessionID: "sess-1", model: STUB_MODEL }, output)

    expect(output.system).toHaveLength(6)
  })

  it("injects all resources for the-pioneer", async () => {
    const tracker = createAgentTracker()
    tracker.track("sess-1", "the-pioneer")
    const hook = createSystemPromptHook(mockCache(), tracker)
    const output = { system: [] as string[] }

    await hook({ sessionID: "sess-1", model: STUB_MODEL }, output)

    expect(output.system).toHaveLength(6)
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

  it("falls back to all resources when sessionID is undefined", async () => {
    const tracker = createAgentTracker()
    const hook = createSystemPromptHook(mockCache(), tracker)
    const output = { system: [] as string[] }

    await hook({ sessionID: undefined, model: STUB_MODEL }, output)

    expect(output.system).toHaveLength(6)
  })

  it("falls back to all resources for untracked session", async () => {
    const tracker = createAgentTracker()
    const hook = createSystemPromptHook(mockCache(), tracker)
    const output = { system: [] as string[] }

    await hook({ sessionID: "unknown-sess", model: STUB_MODEL }, output)

    expect(output.system).toHaveLength(6)
  })
})
