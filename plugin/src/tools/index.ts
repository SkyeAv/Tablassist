import type { ToolDefinition } from "@opencode-ai/plugin";

import type { CliRunner } from "../cli.ts";
import { createApiTools } from "./api.ts";
import { createBiolinkTools } from "./biolink.ts";
import { createFileTools } from "./files.ts";
import { createSchemaTools } from "./schema.ts";

export function createAllTools(cli: CliRunner): Record<string, ToolDefinition> {
  return {
    ...createApiTools(cli),
    ...createBiolinkTools(cli),
    ...createSchemaTools(cli),
    ...createFileTools(cli),
  };
}
