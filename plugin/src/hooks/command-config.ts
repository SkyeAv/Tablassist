import type { Config } from "@opencode-ai/sdk"

type CommandDef = NonNullable<Config["command"]>[string]

const COMMANDS: Record<string, CommandDef> = {
  "tablassist:audit": {
    template: `Audit the Tablassert YAML configuration file at path: {args}

Follow this workflow in order:

1. **Validate structure** — run \`validate-config-file\` on the config. If it fails, note the errors but continue the audit.

2. **Acquire source data** — delegate to \`the-extractor\` to download the source file. Do NOT assume \`source.local\` already exists; the extractor runs the full fallback chain (\`download-pmc-tar\` → S3 via \`pmc-oa-readme\` → web retrieval with mirror/API/cookie strategies) and reports the path where the file landed. If the extractor exhausts every strategy, ask the human for a manual download path and hand it back to the extractor.

3. **Preview source data** — once the file is in hand, delegate column preview to \`the-extractor\` using the reported path.

4. **Evaluate extraction strategy** — for each column mapping, inspect the \`regex\`, \`remove\`, \`prefix\`, \`suffix\`, \`explode_by\`, \`taxon\`, \`prioritize\`, and \`avoid\` fields. Assess whether the transforms will correctly extract clean identifiers from the raw column values you previewed.

5. **Spot-check CURIE resolution** — pick 3–5 representative raw values from the target columns, mentally apply the config's transforms (regex, remove, prefix, etc.), then run \`search-curies\` or \`search-gene-curies\` on the transformed values. Report which resolve and which don't.

6. **Check Biolink alignment and qualifier accuracy** — verify categories and predicates with \`docs-category\`, \`docs-predicate\`, and \`list-predicates\`. Then go further on qualifiers: use \`list-qualifiers\` and \`docs-qualifier\` to evaluate whether each statement's qualifier set scientifically represents what the table and paper actually claim. Flag qualifiers that are missing, wrong, or redundant (e.g. needing \`anatomical_context_qualifier\`, \`causal_mechanism_qualifier\`, \`subject_direction_qualifier\`, \`object_aspect_qualifier\`) so the assertion is scientifically accurate.

7. **Report findings** — organize into two sections:
   - **Structural issues** (schema errors, missing required fields)
   - **Recommended changes** (extraction strategy improvements, Biolink misalignments, CURIE resolution failures, qualifier additions/corrections)

   When surfacing Biolink concepts, briefly explain what they mean for non-specialist readers. Never apply semantic changes without explicit human approval.`,
    description: "Deeply audit a Tablassert YAML config",
    agent: "the-configurator",
  },
  "tablassist:discover": {
    template: `Begin autonomous discover on the topic: {args}

Run in a continuous loop:
1. Search for open-access PMC papers with tabular supplementary data on this topic.
2. For each paper found: download supplements, preview tabular data, spot-check 1-2 transformed identifiers, create one or more Tablassert YAML configs when that is clearer, and validate each config.
3. Write each final YAML into the directory where this command was launched. Use uppercase alphanumeric-only stems, e.g. \`ROMERO3.yaml\`.
4. Put every non-YAML artifact under \`.ledger/<sanitized-topic>/\`. Store downloaded supplements and working files under \`.ledger/<sanitized-topic>/data/PMC<id>/...\` and keep the ledger file there too.
5. Continue processing papers until I tell you to stop.
6. After each paper, report in a minimal tree-style format.

Focus on papers with downloadable Excel, CSV, or TSV supplementary files. One paper or even one supplement may justify multiple configs if that makes the extraction easier to read. Record YAML paths relative to the launch directory when practical.`,
    description: "Autonomously discover papers and create configs on a topic",
    agent: "the-pioneer",
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
