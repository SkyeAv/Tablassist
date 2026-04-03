import { extname } from "node:path";

import type { Hooks } from "@opencode-ai/plugin";

import type { CliDetailedRunner } from "../cli.ts";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export function isYamlPath(filePath: string): boolean {
  const extension = extname(filePath).toLowerCase();
  return extension === ".yaml" || extension === ".yml";
}

export function extractYamlPath(args: unknown): string | null {
  if (typeof args === "string") {
    return isYamlPath(args) ? args : null;
  }

  if (Array.isArray(args)) {
    for (const item of args) {
      const match = extractYamlPath(item);
      if (match) {
        return match;
      }
    }
    return null;
  }

  if (!isRecord(args)) {
    return null;
  }

  const preferredKeys = [
    "filePath",
    "path",
    "file",
    "yaml_file",
    "target",
    "destination",
  ];
  for (const key of preferredKeys) {
    const value = args[key];
    if (typeof value === "string" && isYamlPath(value)) {
      return value;
    }
  }

  for (const value of Object.values(args)) {
    const match = extractYamlPath(value);
    if (match) {
      return match;
    }
  }

  return null;
}

export function buildValidationMessage(validationOutput: string): string {
  const normalized = validationOutput.trim();
  const failed =
    /["']error["']\s*:/i.test(normalized) ||
    /(^|[\s\[{,])error([\s\]}:,]|$)/i.test(normalized) ||
    /validation error/i.test(normalized);

  if (failed) {
    return [
      "--- TABLASSIST VALIDATION ERRORS ---",
      "The YAML file you wrote has validation errors. You MUST fix these errors:",
      normalized,
      "Please correct the file and write it again.",
    ].join("\n");
  }

  return [
    "--- TABLASSIST VALIDATION: PASSED ---",
    normalized || "Validation completed successfully.",
  ].join("\n");
}

export function createYamlValidationHook(
  cli: CliDetailedRunner,
): NonNullable<Hooks["tool.execute.after"]> {
  return async (input, output) => {
    if (input.tool.toLowerCase() !== "write") {
      return;
    }

    const filePath = extractYamlPath(input.args);
    if (!filePath) {
      return;
    }

    const result = await cli("validate-config-file", [filePath]);
    if (result.exitCode !== 0) {
      return;
    }

    const validationOutput = result.stdout.trim();
    if (!validationOutput) {
      return;
    }

    output.output = `${output.output}\n\n${buildValidationMessage(validationOutput)}`;
  };
}
