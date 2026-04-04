import type { Config } from "@opencode-ai/sdk"

type CommandDef = NonNullable<Config["command"]>[string]

const COMMANDS: Record<string, CommandDef> = {
  audit: {
    template:
      "Deeply audit the Tablassert YAML configuration file at path: {args}. First validate the full config with validate-config-file. If validation fails, delegate structural and schema repair to the-builder and preserve valid existing structure. Once the file validates, inspect the config's source, statement, qualifiers, annotations, and provenance, then delegate compact evidence gathering to the-extractor using small data previews and publication/source context as needed. Review subject/object fit, predicate choice, likely missing qualifiers, taxon or category hints, annotation quality, provenance completeness, and whether template-versus-sections structure is appropriate. Report findings in two groups: fixed automatically and recommended changes. Do not apply semantic or scientific edits without explicit user approval.",
    description: "Deeply audit a Tablassert YAML config",
    agent: "the-configurator",
    subtask: true,
  },
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
