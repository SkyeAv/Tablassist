import { tool } from "@opencode-ai/plugin";

import type { CliRunner } from "../cli.ts";
import { createCliTool } from "./shared.ts";

const z = tool.schema;

export function createApiTools(cli: CliRunner) {
  return {
    "search-curies": createCliTool(
      "Search CURIE candidates by term",
      { term: z.string() },
      (args: { term: string }) => cli("search-curies", [args.term]),
    ),
    "get-curie-info": createCliTool(
      "Resolve a single canonical CURIE record",
      { curie: z.string() },
      (args: { curie: string }) => cli("get-curie-info", [args.curie]),
    ),
    "download-pmc-tar": createCliTool(
      "Download and extract a PMC tar archive",
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
  };
}
