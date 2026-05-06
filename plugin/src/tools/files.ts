import { tool } from "@opencode-ai/plugin"

import type { CliRunner } from "../cli.ts"
import { createCliTool } from "./shared.ts"

const z = tool.schema

export function createFileTools(cli: CliRunner) {
  return {
    "extract-text": createCliTool(
      "Extract raw unstructured text from a document file (PDF, DOCX, etc.) via textract. When to use: fast bulk extraction where layout/tables don't matter. Prefer extract-text-semantic when structure matters. Returns extracted text string.",
      { file: z.string(), extension: z.string().optional() },
      (args: { file: string; extension?: string }) =>
        cli("extract-text", [args.file, ...(args.extension ? [args.extension] : [])]),
    ),
    "extract-text-semantic": createCliTool(
      "Extract structured Markdown from a document via Docling (preserves headings, tables, OCR). When to use: tables, figures, or layout matter. Prefer over extract-text when structure matters. Returns Markdown or text.",
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
    "excel-sheets": createCliTool(
      "List sheet names in an Excel file. When to use: before describe-excel/preview-excel when the sheet name is unknown. Returns list of sheet names.",
      { file: z.string() },
      (args: { file: string }) => cli("excel-sheets", [args.file]),
    ),
    "preview-excel": createCliTool(
      "Preview the first N rows of an Excel sheet. When to use: narrow follow-up after describe-excel surfaced something to investigate. Returns {column: [values]} dict.",
      {
        file: z.string(),
        sheet_name: z.string(),
        n_rows: z.number().int().positive(),
      },
      (args: { file: string; sheet_name: string; n_rows: number }) =>
        cli("preview-excel", [args.file, args.sheet_name, String(args.n_rows)]),
    ),
    "preview-csv": createCliTool(
      "Preview the first N rows of a CSV or TSV file. When to use: narrow follow-up after describe-csv surfaced something to investigate. Returns {column: [values]} dict.",
      {
        file: z.string(),
        n_rows: z.number().int().positive(),
        separator: z.string().optional(),
      },
      (args: { file: string; n_rows: number; separator?: string }) =>
        cli("preview-csv", [args.file, String(args.n_rows), ...(args.separator ? [args.separator] : [])]),
    ),
    "describe-excel": createCliTool(
      "Profile an Excel sheet via Polars: schema, sample rows, per-column dtypes/null/unique counts, statistics. When to use: first-pass tabular inspection. Prefer over preview-excel for initial inspection. Returns profile dict.",
      {
        file: z.string(),
        sheet_name: z.string(),
        engine: z.enum(["calamine", "openpyxl", "xlsx2csv"]).optional(),
      },
      (args: { file: string; sheet_name: string; engine?: "calamine" | "openpyxl" | "xlsx2csv" }) =>
        cli("describe-excel", [args.file, args.sheet_name, ...(args.engine ? [args.engine] : [])]),
    ),
    "describe-csv": createCliTool(
      "Profile a CSV or TSV via Polars: schema, sample rows, per-column dtypes/null/unique counts, statistics. When to use: first-pass tabular inspection. Prefer over preview-csv for initial inspection. Returns profile dict.",
      {
        file: z.string(),
        separator: z.string().optional(),
      },
      (args: { file: string; separator?: string }) =>
        cli("describe-csv", [args.file, ...(args.separator ? [args.separator] : [])]),
    ),
  }
}
