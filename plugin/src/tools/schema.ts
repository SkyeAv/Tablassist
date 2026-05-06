import { tool } from "@opencode-ai/plugin"

import type { CliRunner } from "../cli.ts"
import { createCliTool } from "./shared.ts"

const z = tool.schema

export function createSchemaTools(cli: CliRunner) {
  return {
    "section-schema": createCliTool(
      "Return the Section Pydantic model as JSON Schema. When to use: only when the cached schema in the system prompt is insufficient (rare). Returns JSON Schema.",
      {},
      () => cli("section-schema", []),
    ),
    "validate-config-str": createCliTool(
      "Validate a YAML config string (top-level template + optional sections). When to use: validate an unwritten/in-memory draft. Prefer validate-config-file when the YAML is on disk. Returns per-section validation list.",
      { yaml_string: z.string() },
      (args: { yaml_string: string }) => cli("validate-config-str", [args.yaml_string]),
    ),
    "validate-config-file": createCliTool(
      "Validate a Tablassert YAML config file against the Pydantic Section model. When to use: every audit and after every YAML write. Returns per-section validation list.",
      { yaml_file: z.string() },
      (args: { yaml_file: string }) => cli("validate-config-file", [args.yaml_file]),
    ),
  }
}
