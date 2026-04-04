import type { Config } from "@opencode-ai/sdk"

type CommandDef = NonNullable<Config["command"]>[string]

const COMMANDS: Record<string, CommandDef> = {
  "tablassist:audit": {
    template:
      "Deeply audit the Tablassert YAML configuration file at path: {args}. Follow this workflow strictly:\n\n1. Validate the full config with validate-config-file. If validation fails, delegate only structural or schema repair to the-builder, preserving all valid existing structure.\n\n2. Once the file validates, inspect source, statement, qualifiers, annotations, provenance, and template-versus-sections structure.\n\n3. When a PMC identifier is available from the config provenance or context, prioritize download-pmc-tar to fetch the full publication archive before any other evidence gathering.\n\n4. For paper, supplement, or extracted tar content, prefer extract-text-semantic over extract-text so that document structure, reading order, headings, and OCR-aware extraction are preserved.\n\n5. Use smaller data previews (preview-excel, preview-csv) and raw extract-text only as supporting follow-up evidence after the richer sources above have been consulted.\n\n6. Before recommending structural or semantic changes, consult the injected schema, configuration documentation, and relevant Biolink category/predicate/qualifier references to ground every suggestion.\n\n7. Verify audit conclusions against what the plugin and CLI actually validate, so findings are testable and not speculative.\n\nReview focus: subject/object fit, predicate choice, likely missing qualifiers, taxon or category hints, annotation quality, provenance completeness, template-versus-sections suitability, and alignment with current schema/docs/Biolink expectations.\n\nReport findings in exactly two groups: fixed automatically and recommended changes. Do not apply semantic or scientific edits without explicit user approval.",
    description: "Deeply audit a Tablassert YAML config",
    agent: "the-configurator",
    subtask: true,
  },
  "tablassist:validate": {
    template:
      "Validate the Tablassert YAML configuration file at path: {args}. Use the validate-config-file tool. Report whether validation passed or failed, and list any errors.",
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
