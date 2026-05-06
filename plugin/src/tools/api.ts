import { tool } from "@opencode-ai/plugin"

import type { CliRunner } from "../cli.ts"
import { createCliTool } from "./shared.ts"

const z = tool.schema

export function createApiTools(cli: CliRunner) {
  return {
    "search-curies": createCliTool("Search CURIE candidates by term", { term: z.string() }, (args: { term: string }) =>
      cli("search-curies", [args.term]),
    ),
    "download-url": createCliTool(
      "Download a URL into a deterministic artifact directory and return the saved path.",
      { url: z.string(), dest_dir: z.string().optional(), filename: z.string().optional() },
      (args: { url: string; dest_dir?: string; filename?: string }) =>
        cli("download-url", [args.url, ...(args.dest_dir ? [args.dest_dir] : []), ...(args.filename ? ["--filename", args.filename] : [])]),
    ),
    "download-pmc-tar": createCliTool(
      "Download and extract a PMC tar archive into deterministic raw/source artifact directories. Returns the artifact root, extracted source directory, created files, and the specific archive cleanup it performed.",
      { pmc_id: z.number().int(), dest_dir: z.string().optional() },
      (args: { pmc_id: number; dest_dir?: string }) =>
        cli("download-pmc-tar", [String(args.pmc_id), ...(args.dest_dir ? [args.dest_dir] : [])]),
    ),
    "search-gene-curies": createCliTool(
      "Search gene CURIEs within an NCBI taxon",
      { term: z.string(), ncbi_taxon: z.number().int().default(9606) },
      (args: { term: string; ncbi_taxon?: number }) =>
        cli("search-gene-curies", [args.term, String(args.ncbi_taxon ?? 9606)]),
    ),
    "resolve-taxon-id": createCliTool(
      "Resolve an NCBI Taxon ID from an organism name",
      { organism_name: z.string() },
      (args: { organism_name: string }) => cli("resolve-taxon-id", [args.organism_name]),
    ),
    "download-pmc-oa": createCliTool(
      "Download all files for a PMC article (XML, TXT, PDF, JSON metadata, media, supplements) from the PMC Open Access S3 bucket into a deterministic source directory under the requested artifact root. Returns the destination directory, version chosen, and created file list.",
      { pmc_id: z.number().int(), dest_dir: z.string().optional(), version: z.number().int().optional() },
      (args: { pmc_id: number; dest_dir?: string; version?: number }) =>
        cli("download-pmc-oa", [
          String(args.pmc_id),
          ...(args.dest_dir ? [args.dest_dir] : []),
          ...(args.version !== undefined ? ["--version", String(args.version)] : []),
        ]),
    ),
  }
}
