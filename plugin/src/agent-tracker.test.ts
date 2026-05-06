import { describe, expect, it } from "bun:test"

import { RESOURCE_AGENT_KEYS, createAgentTracker } from "./agent-tracker.ts"

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

  it("returns true for the-pioneer", () => {
    const tracker = createAgentTracker()
    tracker.track("sess-1", "the-pioneer")
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

  it("returns false when session is unknown", () => {
    const tracker = createAgentTracker()
    expect(tracker.needsResources("unknown")).toBe(false)
  })

  it("returns false when sessionID is undefined", () => {
    const tracker = createAgentTracker()
    expect(tracker.needsResources(undefined)).toBe(false)
  })
})

describe("getPromptResourceKeys", () => {
  it("returns the full bundle for the-builder", () => {
    const tracker = createAgentTracker()
    tracker.track("sess-1", "the-builder")

    expect(tracker.getPromptResourceKeys("sess-1")).toEqual(RESOURCE_AGENT_KEYS["the-builder"] ?? [])
  })

  it("returns a smaller bundle for the-configurator and pioneer", () => {
    const tracker = createAgentTracker()
    tracker.track("sess-1", "the-configurator")
    tracker.track("sess-2", "the-pioneer")

    expect(tracker.getPromptResourceKeys("sess-1")).toEqual(RESOURCE_AGENT_KEYS["the-configurator"] ?? [])
    expect(tracker.getPromptResourceKeys("sess-2")).toEqual(RESOURCE_AGENT_KEYS["the-pioneer"] ?? [])
  })

  it("returns no resources for extractor and other non-resource agents", () => {
    const tracker = createAgentTracker()
    tracker.track("sess-1", "the-extractor")
    tracker.track("sess-2", "build")

    expect(tracker.getPromptResourceKeys("sess-1")).toEqual([])
    expect(tracker.getPromptResourceKeys("sess-2")).toEqual([])
  })

  it("returns no resources for unknown sessions", () => {
    const tracker = createAgentTracker()

    expect(tracker.getPromptResourceKeys("unknown")).toEqual([])
    expect(tracker.getPromptResourceKeys(undefined)).toEqual([])
  })
})
