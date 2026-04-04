import { describe, expect, it } from "bun:test"

import { RESOURCE_AGENTS, createAgentTracker } from "./agent-tracker.ts"

describe("createAgentTracker", () => {
  it("tracks agent per session", () => {
    const tracker = createAgentTracker()
    tracker.track("sess-1", "the-builder")
    expect(tracker.get("sess-1")).toBe("the-builder")
  })

  it("returns undefined for unknown sessions", () => {
    const tracker = createAgentTracker()
    expect(tracker.get("unknown")).toBeUndefined()
  })

  it("returns undefined when sessionID is undefined", () => {
    const tracker = createAgentTracker()
    expect(tracker.get(undefined)).toBeUndefined()
  })

  it("updates agent when session switches", () => {
    const tracker = createAgentTracker()
    tracker.track("sess-1", "the-builder")
    tracker.track("sess-1", "the-extractor")
    expect(tracker.get("sess-1")).toBe("the-extractor")
  })
})

describe("needsResources", () => {
  it("returns true for the-builder", () => {
    const tracker = createAgentTracker()
    tracker.track("sess-1", "the-builder")
    expect(tracker.needsResources("sess-1")).toBe(true)
  })

  it("returns true for the-configurator", () => {
    const tracker = createAgentTracker()
    tracker.track("sess-1", "the-configurator")
    expect(tracker.needsResources("sess-1")).toBe(true)
  })

  it("returns false for the-extractor", () => {
    const tracker = createAgentTracker()
    tracker.track("sess-1", "the-extractor")
    expect(tracker.needsResources("sess-1")).toBe(false)
  })

  it("returns false for non-tablassist agents", () => {
    const tracker = createAgentTracker()
    tracker.track("sess-1", "build")
    expect(tracker.needsResources("sess-1")).toBe(false)
    tracker.track("sess-2", "plan")
    expect(tracker.needsResources("sess-2")).toBe(false)
  })

  it("falls back to true when session is unknown", () => {
    const tracker = createAgentTracker()
    expect(tracker.needsResources("unknown")).toBe(true)
  })

  it("falls back to true when sessionID is undefined", () => {
    const tracker = createAgentTracker()
    expect(tracker.needsResources(undefined)).toBe(true)
  })
})

describe("RESOURCE_AGENTS", () => {
  it("contains exactly the-builder and the-configurator", () => {
    expect(RESOURCE_AGENTS.size).toBe(2)
    expect(RESOURCE_AGENTS.has("the-builder")).toBe(true)
    expect(RESOURCE_AGENTS.has("the-configurator")).toBe(true)
    expect(RESOURCE_AGENTS.has("the-extractor")).toBe(false)
  })
})
