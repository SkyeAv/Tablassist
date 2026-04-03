import { tool } from "@opencode-ai/plugin";

import type { CliRunner } from "../cli.ts";
import { createCliTool } from "./shared.ts";

const z = tool.schema;

export function createSchemaTools(cli: CliRunner) {
  return {
    "section-schema": createCliTool("Return the Section Pydantic model as JSON schema", {}, () => cli("section-schema", [])),
    "validate-section-str": createCliTool(
      "Validate a single YAML section from string",
      { yaml_string: z.string() },
      (args: { yaml_string: string }) => cli("validate-section-str", [args.yaml_string]),
    ),
    "validate-config-str": createCliTool(
      "Validate a full YAML config from string",
      { yaml_string: z.string() },
      (args: { yaml_string: string }) => cli("validate-config-str", [args.yaml_string]),
    ),
    "validate-config-file": createCliTool(
      "Validate a full YAML config from file path",
      { yaml_file: z.string() },
      (args: { yaml_file: string }) => cli("validate-config-file", [args.yaml_file]),
    ),
  };
}
