import { describe, expect, it } from "bun:test"

import { CLI_ERROR_PREFIX } from "../cli.ts"
import { createCliTool } from "./shared.ts"

type ToolLike = {
  execute: (input: Record<string, unknown>, context: { metadata: (value: unknown) => void }) => Promise<string>
}

describe("createCliTool", () => {
  it("sets normal title for successful execution", async () => {
    const tool = createCliTool("Fetch data", {}, async () => '{"result": "ok"}') as unknown as ToolLike
    let capturedMeta: unknown
    await tool.execute(
      {},
      {
        metadata(v) {
          capturedMeta = v
        },
      },
    )
    expect(capturedMeta).toEqual({ title: "Fetch data" })
  })

  it("sets error title when output starts with ERROR prefix", async () => {
    const tool = createCliTool(
      "Fetch data",
      {},
      async () => `${CLI_ERROR_PREFIX}connection refused`,
    ) as unknown as ToolLike
    let capturedMeta: unknown
    const result = await tool.execute(
      {},
      {
        metadata(v) {
          capturedMeta = v
        },
      },
    )
    expect(capturedMeta).toEqual({ title: "Error: Fetch data" })
    expect(result).toContain("connection refused")
  })

  it("still returns full error string for agent consumption", async () => {
    const errorMsg = `${CLI_ERROR_PREFIX}invalid CURIE format`
    const tool = createCliTool("Resolve CURIE", {}, async () => errorMsg) as unknown as ToolLike
    const result = await tool.execute(
      {},
      {
        metadata() {},
      },
    )
    expect(result).toBe(errorMsg)
  })
})
