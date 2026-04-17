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
      subtask: true,
    })
  })

  it("tablassist:audit template validates first", async () => {
    const hook = createCommandConfigHook()
    const config: Config = {}
    await hook(config)
    const template: string = config.command?.["tablassist:audit"]?.template ?? ""

    expect(template).toContain("validate-config-file")
    expect(template).toContain("Validate the full config")
  })

  it("tablassist:audit template prioritizes download-pmc-tar", async () => {
    const hook = createCommandConfigHook()
    const config: Config = {}
    await hook(config)
    const template: string = config.command?.["tablassist:audit"]?.template ?? ""

    expect(template).toContain("download-pmc-tar")
    expect(template).toContain("prioritize")
  })

  it("tablassist:audit template requires pmc-oa-readme with AWS CLI execution before direct web retrieval", async () => {
    const hook = createCommandConfigHook()
    const config: Config = {}
    await hook(config)
    const template: string = config.command?.["tablassist:audit"]?.template ?? ""

    expect(template).toContain("pmc-oa-readme")
    expect(template).toContain("execute")
    expect(template).toContain("AWS CLI")
    expect(template).toContain("bash")
    expect(template).toContain("aws s3 cp --no-sign-request")
    expect(template).toContain("Only if the AWS CLI download also fails")
    expect(template).toContain("direct web retrieval")
  })

  it("tablassist:audit template prefers extract-text-semantic", async () => {
    const hook = createCommandConfigHook()
    const config: Config = {}
    await hook(config)
    const template: string = config.command?.["tablassist:audit"]?.template ?? ""

    expect(template).toContain("extract-text-semantic")
    expect(template).toContain("prefer extract-text-semantic over extract-text")
  })

  it("tablassist:audit template checks schema/docs/Biolink context", async () => {
    const hook = createCommandConfigHook()
    const config: Config = {}
    await hook(config)
    const template: string = config.command?.["tablassist:audit"]?.template ?? ""

    expect(template).toContain("schema")
    expect(template).toContain("Biolink")
    expect(template).toContain("documentation")
  })

  it("tablassist:audit template forbids unapproved semantic edits", async () => {
    const hook = createCommandConfigHook()
    const config: Config = {}
    await hook(config)
    const template: string = config.command?.["tablassist:audit"]?.template ?? ""

    expect(template).toContain("Do not apply semantic or scientific edits without explicit user approval")
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

  it("tablassist:validate template requires three-step PMC retrieval chain", async () => {
    const hook = createCommandConfigHook()
    const config: Config = {}
    await hook(config)
    const template: string = config.command?.["tablassist:validate"]?.template ?? ""

    expect(template).toContain("validate-config-file")
    expect(template).toContain("pmc-oa-readme")
    expect(template).toContain("execute")
    expect(template).toContain("AWS CLI")
    expect(template).toContain("bash")
    expect(template).toContain("Only if the AWS CLI download also fails")
    expect(template).toContain("direct web retrieval")
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
