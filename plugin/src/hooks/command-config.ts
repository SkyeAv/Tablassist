import type { Config } from "@opencode-ai/sdk"

type CommandDef = NonNullable<Config["command"]>[string]

const COMMANDS: Record<string, CommandDef> = {
  "tablassist:audit": {
    template:
      "Deeply audit the Tablassert YAML configuration file at path: {args}. Execute your standard audit workflow: validate the config, review components, delegate evidence extraction (including PMC fetching) to the-extractor, and report findings to the user. Recommend semantic changes but wait for approval before applying them.",
    description: "Deeply audit a Tablassert YAML config",
    agent: "the-configurator",
  },
  "tablassist:validate": {
    template:
      "Validate the Tablassert YAML configuration file at path: {args}. Use validate-config-file to check the file. Fix any structural or schema errors you encounter, preserving valid existing structure. Report the final validation status and any remaining issues.",
    description: "Validate a Tablassert YAML config file",
    agent: "the-builder",
    subtask: true,
  },
  "tablassist:preview": {
    template:
      "Preview the data file at: {args}. If it is an Excel file (.xlsx, .xls), first list the sheet names using the excel-sheets tool, then preview the first 10 rows of each sheet using the preview-excel tool. If it is a CSV or TSV file, preview the first 10 rows using the preview-csv tool. Present the data clearly.",
    description: "Preview rows from a CSV, TSV, or Excel file",
    agent: "the-extractor",
    subtask: true,
  },
  "tablassist:search": {
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
