import { tool } from "@opencode-ai/plugin"

import type { CliRunner } from "../cli.ts"
import { createCliTool } from "./shared.ts"

const z = tool.schema

export function createBiolinkTools(cli: CliRunner) {
  return {
    "list-categories": createCliTool(
      "List all supported Biolink categories. When to use: enumerate the valid set before recommending a category. Returns JSON list of strings.",
      {},
      () => cli("list-categories", []),
    ),
    "list-predicates": createCliTool(
      "List all supported Biolink predicates. When to use: enumerate the valid set before recommending a predicate. Returns JSON list of strings.",
      {},
      () => cli("list-predicates", []),
    ),
    "list-qualifiers": createCliTool(
      "List all supported Biolink qualifiers. When to use: enumerate the valid set before recommending a qualifier. Returns JSON list of strings.",
      {},
      () => cli("list-qualifiers", []),
    ),
    "docs-category": createCliTool(
      "Fetch Biolink documentation for one category. When to use: validate that a specific category scientifically fits. Prefer over web search. Returns Markdown.",
      { category: z.string() },
      (args: { category: string }) => cli("docs-category", [args.category]),
    ),
    "docs-predicate": createCliTool(
      "Fetch Biolink documentation for one predicate. When to use: validate that a specific predicate scientifically fits. Prefer over web search. Returns Markdown.",
      { predicate: z.string() },
      (args: { predicate: string }) => cli("docs-predicate", [args.predicate]),
    ),
    "docs-qualifier": createCliTool(
      "Fetch Biolink documentation for one qualifier. When to use: validate that a specific qualifier scientifically fits. Prefer over web search. Returns Markdown.",
      { qualifier: z.string() },
      (args: { qualifier: string }) => cli("docs-qualifier", [args.qualifier]),
    ),
  }
}
