import { tool } from "@opencode-ai/plugin"

import type { CliRunner } from "../cli.ts"
import { createCliTool } from "./shared.ts"

const z = tool.schema

export function createDiscoverTools(cli: CliRunner) {
  return {
    "search-pmc": createCliTool(
      "Search PMC for open-access articles on a topic. Returns ranked papers; triage supplements with get-pmc-summary.",
      {
        query: z.string(),
        max_results: z.number().int().positive().default(10),
        page: z.number().int().nonnegative().default(0),
      },
      (args: { query: string; max_results?: number; page?: number }) =>
        cli("search-pmc", [args.query, String(args.max_results ?? 10), String(args.page ?? 0)]),
    ),
    "get-pmc-summary": createCliTool(
      "Fetch detailed metadata and supplement list for a PMC article",
      { pmc_id: z.number().int() },
      (args: { pmc_id: number }) => cli("get-pmc-summary", [String(args.pmc_id)]),
    ),
    "discovery-ledger": createCliTool(
      "Manage discovery progress ledger (read/add/check). Ledger tracks processed PMCIDs so the pipeline survives context resets.",
      {
        action: z.enum(["read", "add", "check"]),
        ledger_path: z.string(),
        pmc_id: z.number().int().optional(),
        status: z.string().optional(),
        summary: z.string().optional(),
        topic: z.string().optional(),
        config_paths: z.array(z.string()).optional(),
        config_path: z.string().optional(),
      },
      (args: {
        action: "read" | "add" | "check"
        ledger_path: string
        pmc_id?: number
        status?: string
        summary?: string
        topic?: string
        config_paths?: string[]
        config_path?: string
      }) =>
        cli("discovery-ledger", [
          args.action,
          args.ledger_path,
          ...(args.pmc_id != null ? ["--pmc-id", String(args.pmc_id)] : []),
          ...(args.status ? ["--status", args.status] : []),
          ...(args.summary ? ["--summary", args.summary] : []),
          ...(args.topic ? ["--topic", args.topic] : []),
          ...(args.config_paths?.length ? args.config_paths.flatMap((path) => ["--config-paths", path]) : []),
          ...(args.config_path ? ["--config-path", args.config_path] : []),
        ]),
    ),
  }
}
