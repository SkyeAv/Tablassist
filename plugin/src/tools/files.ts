import { tool } from "@opencode-ai/plugin"

import type { CliRunner } from "../cli.ts"
import { createCliTool } from "./shared.ts"

const z = tool.schema

export function createFileTools(cli: CliRunner) {
  return {
    "extract-text": createCliTool(
      "Extract text from PDF, DOCX, and similar files",
      { file: z.string(), extension: z.string().optional() },
      (args: { file: string; extension?: string }) =>
        cli("extract-text", [args.file, ...(args.extension ? [args.extension] : [])]),
    ),
    "extract-text-semantic": createCliTool(
      "Extract semantic Markdown or text with Docling",
      {
        file: z.string(),
        output_format: z.enum(["markdown", "text"]).optional(),
        ocr: z.enum(["auto", "off", "on"]).optional(),
      },
      (args: { file: string; output_format?: "markdown" | "text"; ocr?: "auto" | "off" | "on" }) => {
        const outputFormat = args.output_format ?? (args.ocr ? "markdown" : undefined)
        return cli("extract-text-semantic", [
          args.file,
          ...(outputFormat ? [outputFormat] : []),
          ...(args.ocr ? [args.ocr] : []),
        ])
      },
    ),
    "excel-sheets": createCliTool("List sheet names in an Excel file", { file: z.string() }, (args: { file: string }) =>
      cli("excel-sheets", [args.file]),
    ),
    "preview-excel": createCliTool(
      "Preview the first N rows of an Excel sheet as JSON",
      {
        file: z.string(),
        sheet_name: z.string(),
        n_rows: z.number().int().positive(),
      },
      (args: { file: string; sheet_name: string; n_rows: number }) =>
        cli("preview-excel", [args.file, args.sheet_name, String(args.n_rows)]),
    ),
    "preview-csv": createCliTool(
      "Preview the first N rows of a CSV or TSV file as JSON",
      {
        file: z.string(),
        n_rows: z.number().int().positive(),
        separator: z.string().optional(),
      },
      (args: { file: string; n_rows: number; separator?: string }) =>
        cli("preview-csv", [args.file, String(args.n_rows), ...(args.separator ? [args.separator] : [])]),
    ),
    "describe-excel": createCliTool(
      "Inspect an Excel sheet with Polars: schema, sample rows, null counts, unique values, and per-column statistics",
      {
        file: z.string(),
        sheet_name: z.string(),
        engine: z.enum(["calamine", "openpyxl", "xlsx2csv"]).optional(),
      },
      (args: { file: string; sheet_name: string; engine?: "calamine" | "openpyxl" | "xlsx2csv" }) =>
        cli("describe-excel", [args.file, args.sheet_name, ...(args.engine ? [args.engine] : [])]),
    ),
    "describe-csv": createCliTool(
      "Inspect a CSV or TSV with Polars: schema, sample rows, null counts, unique values, and per-column statistics",
      {
        file: z.string(),
        separator: z.string().optional(),
      },
      (args: { file: string; separator?: string }) =>
        cli("describe-csv", [args.file, ...(args.separator ? [args.separator] : [])]),
    ),
  }
}
