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

    expect(template).toContain("validate the config")
    expect(template).toContain("delegate evidence extraction")
    expect(template).toContain("wait for approval")
  })

  it("registers tablassist:validate, tablassist:preview, and tablassist:search", async () => {
    const hook = createCommandConfigHook()
    const config: Config = {}
    await hook(config)
    const commands = config.command

    expect(commands?.["tablassist:validate"]).toMatchObject({
      description: "Validate a Tablassert YAML config file",
      agent: "the-builder",
      subtask: true,
    })
    expect(commands?.["tablassist:preview"]).toMatchObject({
      description: "Preview rows from a CSV, TSV, or Excel file",
      agent: "the-extractor",
      subtask: true,
    })
    expect(commands?.["tablassist:search"]).toMatchObject({
      description: "Search CURIE candidates by term",
      agent: "the-extractor",
      subtask: true,
    })
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
