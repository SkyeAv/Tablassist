import { describe, expect, it } from "bun:test"
import type { Config } from "@opencode-ai/sdk"

import { createCommandConfigHook } from "./command-config.ts"

describe("createCommandConfigHook", () => {
  it("registers the audit command alongside existing commands", async () => {
    const hook = createCommandConfigHook()
    const config: Config = {
      command: {
        existing: {
          template: "existing template",
          description: "existing description",
        },
      },
    }

    await hook(config)
    const commands = config.command

    expect(commands).toBeDefined()
    expect(commands?.existing).toEqual({
      template: "existing template",
      description: "existing description",
    })
    expect(commands?.audit).toMatchObject({
      description: "Deeply audit a Tablassert YAML config",
      agent: "the-configurator",
      subtask: true,
    })
    expect(commands?.audit?.template).toContain("fixed automatically")
    expect(commands?.audit?.template).toContain("Do not apply semantic or scientific edits")
    expect(commands?.validate).toBeDefined()
    expect(commands?.preview).toBeDefined()
    expect(commands?.search).toBeDefined()
  })
})
