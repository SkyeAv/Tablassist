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
      "Read or mutate the discovery ledger (read/add/check/claim/release). When to use: the-pioneer batch workflows for cross-session state and concurrent claim coordination. On `add`, pass paper_url (from search-pmc/get-pmc-summary) and s3_uri (from download-pmc-oa) so downstream readers cite real, observed URLs. If paper_url is omitted, the ledger defaults to the canonical PMC URL for the given pmc_id. Pass datalake_manifest (the array returned by consolidate-datalake) so the ledger records which files were relocated. Returns action-shaped dict.",
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
        datalake_manifest: z
          .array(
            z.object({
              config_path: z.string(),
              original_path: z.string(),
              datalake_path: z.string(),
            }),
          )
          .optional(),
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
        datalake_manifest?: { config_path: string; original_path: string; datalake_path: string }[]
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
          ...(args.datalake_manifest?.length ? ["--datalake-manifest", JSON.stringify(args.datalake_manifest)] : []),
        ]),
    ),
    "consolidate-datalake": createCliTool(
      "Move files referenced by `source.local` in one or more YAML configs into a flat `./DATALAKE/` next to the configs, renaming each `PMC{pmc_id}_{basename}`, and rewrite `source.local` to `./DATALAKE/PMC{pmc_id}_{basename}`. When to use: the-pioneer's per-paper finalization, after `the-builder` writes configs but before `discovery-ledger add`. Idempotent — safe to re-run. Returns `{status, datalake_root, manifest: [{config_path, original_path, datalake_path}]}`. Forward `manifest` verbatim to `discovery-ledger add` as `datalake_manifest`.",
      {
        yaml_files: z.array(z.string()).min(1),
        pmc_id: z.number().int(),
        artifact_root: z.string(),
        launch_dir: z.string().optional(),
      },
      (args: { yaml_files: string[]; pmc_id: number; artifact_root: string; launch_dir?: string }) =>
        cli("consolidate-datalake", [
          ...args.yaml_files,
          "--pmc-id",
          String(args.pmc_id),
          "--artifact-root",
          args.artifact_root,
          ...(args.launch_dir ? ["--launch-dir", args.launch_dir] : []),
        ]),
    ),
  }
}
