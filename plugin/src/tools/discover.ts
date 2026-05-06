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
      "Manage discovery progress ledger (read/add/check/claim/release). Ledger tracks per-paper outcomes and active claims so concurrent agents can share a topic safely across context resets.",
      {
        action: z.enum(["read", "add", "check", "claim", "release"]),
        ledger_path: z.string(),
        pmc_id: z.number().int().optional(),
        status: z.string().optional(),
        summary: z.string().optional(),
        topic: z.string().optional(),
        config_paths: z.array(z.string()).optional(),
        config_path: z.string().optional(),
        artifact_root: z.string().optional(),
        agent_name: z.string().optional(),
        run_id: z.string().optional(),
        lease_seconds: z.number().int().positive().optional(),
      },
      (args: {
        action: "read" | "add" | "check" | "claim" | "release"
        ledger_path: string
        pmc_id?: number
        status?: string
        summary?: string
        topic?: string
        config_paths?: string[]
        config_path?: string
        artifact_root?: string
        agent_name?: string
        run_id?: string
        lease_seconds?: number
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
          ...(args.artifact_root ? ["--artifact-root", args.artifact_root] : []),
          ...(args.agent_name ? ["--agent-name", args.agent_name] : []),
          ...(args.run_id ? ["--run-id", args.run_id] : []),
          ...(args.lease_seconds !== undefined ? ["--lease-seconds", String(args.lease_seconds)] : []),
        ]),
    ),
  }
}
