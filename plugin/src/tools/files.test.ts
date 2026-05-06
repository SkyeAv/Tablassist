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

  it("passes optional separator through for CSV description", async () => {
    const tools = createFileTools(async (command, args) => `${command}:${args.join(",")}`)
    const describeCsvTool = tools["describe-csv"] as unknown as ToolLike

    const result = await describeCsvTool.execute({ file: "table.tsv", separator: "\t" }, { metadata: () => {} })

    expect(result).toBe("describe-csv:table.tsv,\t")
  })

  it("keeps Excel description args in CLI order", async () => {
    const tools = createFileTools(async (command, args) => `${command}:${args.join(",")}`)
    const describeExcelTool = tools["describe-excel"] as unknown as ToolLike

    const result = await describeExcelTool.execute(
      { file: "table.xlsx", sheet_name: "Sheet1", engine: "openpyxl" },
      { metadata: () => {} },
    )

    expect(result).toBe("describe-excel:table.xlsx,Sheet1,openpyxl")
  })
})
