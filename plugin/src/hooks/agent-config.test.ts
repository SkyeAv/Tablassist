import { describe, expect, it } from "bun:test"
import type { Config } from "@opencode-ai/sdk"

import { createAgentConfigHook } from "./agent-config.ts"

describe("createAgentConfigHook", () => {
  it("loads agent tool toggles with hyphenated tool names", async () => {
    const hook = createAgentConfigHook()
    const config: Config = {}

    await hook(config)

    const configurator = config.agent?.["the-configurator"]
    const builder = config.agent?.["the-builder"]
    const pioneer = config.agent?.["the-pioneer"]

    expect(configurator?.tools?.["describe-csv"]).toBe(false)
    expect(configurator?.tools?.["search-curies"]).toBe(false)
    expect(builder?.tools?.["describe-excel"]).toBe(false)
    expect(pioneer?.tools?.["download-pmc-oa"]).toBe(false)
  })
})
