import type { Config } from "@opencode-ai/sdk"

type CommandDef = NonNullable<Config["command"]>[string]

const COMMANDS: Record<string, CommandDef> = {
  validate: {
    template:
      "Validate the Tablassert YAML configuration file at path: {args}. Use the validate-config-file tool. Report whether validation passed or failed, and list any errors.",
    description: "Validate a Tablassert YAML config file",
    agent: "the-builder",
    subtask: true,
  },
  preview: {
    template:
      "Preview the data file at: {args}. If it is an Excel file (.xlsx, .xls), first list the sheet names using the excel-sheets tool, then preview the first 10 rows of each sheet using the preview-excel tool. If it is a CSV or TSV file, preview the first 10 rows using the preview-csv tool. Present the data clearly.",
    description: "Preview rows from a CSV, TSV, or Excel file",
    agent: "the-extractor",
    subtask: true,
  },
  search: {
    template:
      "Search for CURIE candidates matching the term: {args}. Use the search-curies tool. Present the results as a concise list showing each candidate's CURIE identifier, name, and category.",
    description: "Search CURIE candidates by term",
    agent: "the-extractor",
    subtask: true,
  },
}

export function createCommandConfigHook(): (config: Config) => Promise<void> {
  return async (config) => {
    const existing = config.command ?? {}
    config.command = { ...existing, ...COMMANDS }
  }
}
