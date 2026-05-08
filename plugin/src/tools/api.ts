import { tool } from "@opencode-ai/plugin"

import type { CliRunner } from "../cli.ts"
import { createCliTool } from "./shared.ts"

const z = tool.schema

export function createApiTools(cli: CliRunner) {
  return {
    "search-curies": createCliTool(
      "Search CURIE candidates by free-text term via Configurator API. When to use: resolve any non-gene entity. Prefer search-gene-curies when the category is Gene or the prefix is NCBIGene/HGNC/Ensembl. Returns ranked CURIE list.",
      { term: z.string() },
      (args: { term: string }) => cli("search-curies", [args.term]),
    ),
    "download-url": createCliTool(
      "Download a URL into the artifact directory. When to use: web/publisher fallback after both PMC download tools fail. Pass URLs that came from a real tool response (paper_url, supplement url, s3_https_uri, scraped href) — never construct or guess URLs. Returns {url, path, content_type}.",
      { url: z.string(), dest_dir: z.string().optional(), filename: z.string().optional() },
      (args: { url: string; dest_dir?: string; filename?: string }) =>
        cli("download-url", [
          args.url,
          ...(args.dest_dir ? [args.dest_dir] : []),
          ...(args.filename ? ["--filename", args.filename] : []),
        ]),
    ),
    "download-pmc-tar": createCliTool(
      "Download and extract a PMC tar archive by PMC ID. When to use: first-choice PMC retrieval before download-pmc-oa. Returns {pmcid, artifact_root, source_dir, files, source_url, paper_url}. Quote paper_url verbatim in any failure report — do not construct your own.",
      { pmc_id: z.number().int(), dest_dir: z.string().optional() },
      (args: { pmc_id: number; dest_dir?: string }) =>
        cli("download-pmc-tar", [String(args.pmc_id), ...(args.dest_dir ? [args.dest_dir] : [])]),
    ),
    "search-gene-curies": createCliTool(
      "Search gene CURIEs scoped to an NCBI taxon. When to use: category is Gene or prefix is NCBIGene/HGNC/Ensembl. Prefer over search-curies for gene resolution. Returns ranked CURIE list.",
      { term: z.string(), ncbi_taxon: z.number().int().default(9606) },
      (args: { term: string; ncbi_taxon?: number }) =>
        cli("search-gene-curies", [args.term, String(args.ncbi_taxon ?? 9606)]),
    ),
    "resolve-taxon-id": createCliTool(
      "Resolve an NCBI Taxon ID from an organism name. When to use: verifying a taxon constraint before recommending it. Returns {taxon_id, name}.",
      { organism_name: z.string() },
      (args: { organism_name: string }) => cli("resolve-taxon-id", [args.organism_name]),
    ),
    "download-pmc-oa": createCliTool(
      "Download all PMC OA files (XML, PDF, supplements, media) from S3 by PMC ID. When to use: fallback when download-pmc-tar fails (404/400/conn) and the article is in OA. Returns {pmcid, version, prefix, source_dir, files, available_versions, s3_uri, s3_https_uri, paper_url}. Quote s3_uri/s3_https_uri/paper_url verbatim in any failure report or ledger entry — do not construct your own URL by analogy.",
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
