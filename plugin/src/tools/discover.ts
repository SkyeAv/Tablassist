import { tool } from "@opencode-ai/plugin"

import type { CliRunner } from "../cli.ts"
import { createCliTool } from "./shared.ts"

const z = tool.schema

export function createDiscoverTools(cli: CliRunner) {
  return {
    "search-pmc": createCliTool(
      "Search PubMed Central for open-access articles. When to use: literature discovery on a topic. Triage candidates with get-pmc-summary. Returns {count, papers: [{pmcid, title, authors, date, paper_url}]}. Forward paper_url verbatim to downstream agents instead of constructing PMC URLs yourself.",
      {
        query: z.string(),
        max_results: z.number().int().positive().default(10),
        page: z.number().int().nonnegative().default(0),
      },
      (args: { query: string; max_results?: number; page?: number }) =>
        cli("search-pmc", [args.query, String(args.max_results ?? 10), String(args.page ?? 0)]),
    ),
    "get-pmc-summary": createCliTool(
      "Fetch metadata and supplements list for one PMC article. When to use: triage after search-pmc returned a candidate. Returns {pmcid, title, abstract, authors, paper_url, supplements: [{filename, media_type, url}]}. Each supplement url is the canonical PMC `bin/` URL — pass these to download-url verbatim instead of constructing your own.",
      { pmc_id: z.number().int() },
      (args: { pmc_id: number }) => cli("get-pmc-summary", [String(args.pmc_id)]),
    ),
    "discovery-ledger": createCliTool(
      "Read or mutate the discovery ledger (read/add/check/claim/release). When to use: the-pioneer batch workflows for cross-session state and concurrent claim coordination. On `add`, pass paper_url (from search-pmc/get-pmc-summary) and s3_uri (from download-pmc-oa) so downstream readers cite real, observed URLs. If paper_url is omitted, the ledger defaults to the canonical PMC URL for the given pmc_id. Returns action-shaped dict.",
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
        paper_url: z.string().optional(),
        s3_uri: z.string().optional(),
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
        paper_url?: string
        s3_uri?: string
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
          ...(args.paper_url ? ["--paper-url", args.paper_url] : []),
          ...(args.s3_uri ? ["--s3-uri", args.s3_uri] : []),
        ]),
    ),
  }
}
