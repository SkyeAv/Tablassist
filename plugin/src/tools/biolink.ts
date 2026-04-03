import { tool } from "@opencode-ai/plugin";

import type { CliRunner } from "../cli.ts";
import { createCliTool } from "./shared.ts";

const z = tool.schema;

export function createBiolinkTools(cli: CliRunner) {
  return {
    "list-categories": createCliTool(
      "List all supported Biolink categories",
      {},
      () => cli("list-categories", []),
    ),
    "list-predicates": createCliTool(
      "List all supported Biolink predicates",
      {},
      () => cli("list-predicates", []),
    ),
    "list-qualifiers": createCliTool(
      "List all supported Biolink qualifiers",
      {},
      () => cli("list-qualifiers", []),
    ),
    "docs-category": createCliTool(
      "Fetch Biolink docs for a category",
      { category: z.string() },
      (args: { category: string }) => cli("docs-category", [args.category]),
    ),
    "docs-predicate": createCliTool(
      "Fetch Biolink docs for a predicate",
      { predicate: z.string() },
      (args: { predicate: string }) => cli("docs-predicate", [args.predicate]),
    ),
    "docs-qualifier": createCliTool(
      "Fetch Biolink docs for a qualifier",
      { qualifier: z.string() },
      (args: { qualifier: string }) => cli("docs-qualifier", [args.qualifier]),
    ),
  };
}
