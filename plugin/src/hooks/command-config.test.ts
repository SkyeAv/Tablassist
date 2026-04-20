import { describe, expect, it } from "bun:test"
import type { Config } from "@opencode-ai/sdk"

import { createCommandConfigHook } from "./command-config.ts"

describe("createCommandConfigHook", () => {
  it("registers namespaced tablassist: commands and preserves existing commands", async () => {
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
  })

  it("registers tablassist:audit with correct metadata", async () => {
    const hook = createCommandConfigHook()
    const config: Config = {}
    await hook(config)
    const audit = config.command?.["tablassist:audit"]

    expect(audit).toMatchObject({
      description: "Deeply audit a Tablassert YAML config",
      agent: "the-configurator",
    })
    expect(audit?.subtask).toBeUndefined()
  })

  it("tablassist:audit template includes standard workflow instructions", async () => {
    const hook = createCommandConfigHook()
    const config: Config = {}
    await hook(config)
    const template: string = config.command?.["tablassist:audit"]?.template ?? ""

    expect(template).toContain("validate-config-file")
    expect(template).toContain("Spot-check CURIE resolution")
    expect(template).toContain("without explicit human approval")
  })

  it("registers tablassist:validate with correct metadata", async () => {
    const hook = createCommandConfigHook()
    const config: Config = {}
    await hook(config)
    const commands = config.command

    expect(commands?.["tablassist:validate"]).toMatchObject({
      description: "Validate a Tablassert YAML config file (structural only)",
      agent: "the-builder",
      subtask: true,
    })
    expect(commands?.["tablassist:preview"]).toBeUndefined()
    expect(commands?.["tablassist:search"]).toBeUndefined()
  })

  it("tablassist:validate template includes validation instructions", async () => {
    const hook = createCommandConfigHook()
    const config: Config = {}
    await hook(config)
    const template: string = config.command?.["tablassist:validate"]?.template ?? ""

    expect(template).toContain("validate-config-file")
    expect(template).toContain("Fix any structural or schema errors")
  })

  it("does not register unprefixed command keys", async () => {
    const hook = createCommandConfigHook()
    const config: Config = {}
    await hook(config)
    const commands = config.command

    expect(commands?.audit).toBeUndefined()
    expect(commands?.validate).toBeUndefined()
    expect(commands?.preview).toBeUndefined()
    expect(commands?.search).toBeUndefined()
  })
})
