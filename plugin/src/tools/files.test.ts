import { describe, expect, it } from "bun:test"

import { createFileTools } from "./files.ts"

type ToolLike = {
  execute: (input: Record<string, unknown>, context: { metadata: (_value: unknown) => void }) => Promise<string>
}

describe("createFileTools", () => {
  it("passes semantic extraction defaults through without forcing extra args", async () => {
    const tools = createFileTools(async (command, args) => `${command}:${args.join(",")}`)
    const semanticTool = tools["extract-text-semantic"] as unknown as ToolLike

    const result = await semanticTool.execute({ file: "paper.pdf" }, { metadata: () => {} })

    expect(result).toBe("extract-text-semantic:paper.pdf")
  })

  it("preserves output format and OCR argument order for semantic extraction", async () => {
    const tools = createFileTools(async (command, args) => `${command}:${args.join(",")}`)
    const semanticTool = tools["extract-text-semantic"] as unknown as ToolLike

    const result = await semanticTool.execute(
      { file: "scan.pdf", output_format: "text", ocr: "on" },
      { metadata: () => {} },
    )

    expect(result).toBe("extract-text-semantic:scan.pdf,text,on")
  })
})
