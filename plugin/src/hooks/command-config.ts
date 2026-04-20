import type { Config } from "@opencode-ai/sdk"

type CommandDef = NonNullable<Config["command"]>[string]

const COMMANDS: Record<string, CommandDef> = {
  "tablassist:audit": {
    template: `Audit the Tablassert YAML configuration file at path: {args}

Follow this workflow in order:

1. **Validate structure** — run \`validate-config-file\` on the config. If it fails, note the errors but continue the audit.

2. **Preview source data** — read the config to find the \`source.local\` file path, then use \`preview-csv\` or \`preview-excel\` to inspect the first rows of actual column data.

3. **Evaluate extraction strategy** — for each column mapping, inspect the \`regex\`, \`remove\`, \`prefix\`, \`suffix\`, \`explode_by\`, \`taxon\`, \`prioritize\`, and \`avoid\` fields. Assess whether the transforms will correctly extract clean identifiers from the raw column values you previewed.

4. **Spot-check CURIE resolution** — pick 3–5 representative raw values from the target columns, mentally apply the config's transforms (regex, remove, prefix, etc.), then run \`search-curies\` or \`search-gene-curies\` on the transformed values. Report which resolve and which don't.

5. **Check Biolink alignment** — verify categories, predicates, and qualifiers are appropriate using \`docs-category\` and \`docs-predicate\`. Flag any mismatches.

6. **Report findings** — organize into two sections:
   - **Structural issues** (schema errors, missing required fields)
   - **Recommended changes** (extraction strategy improvements, Biolink misalignments, CURIE resolution failures)

   When surfacing Biolink concepts, briefly explain what they mean for non-specialist readers. Never apply semantic changes without explicit human approval.`,
    description: "Deeply audit a Tablassert YAML config",
    agent: "the-configurator",
  },
  "tablassist:validate": {
    template:
      "Validate the Tablassert YAML configuration file at path: {args}. Run validate-config-file. Fix any structural or schema errors, preserving valid existing structure. Report pass/fail status and list any remaining issues. Do NOT perform CURIE lookups or semantic review — keep this fast and structural only.",
    description: "Validate a Tablassert YAML config file (structural only)",
    agent: "the-builder",
    subtask: true,
  },
}

export function createCommandConfigHook(): (config: Config) => Promise<void> {
  return async (config) => {
    const existing = config.command ?? {}
    config.command = { ...existing, ...COMMANDS }
  }
}
