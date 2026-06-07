# @skyeav/tablassist

[![npm](https://img.shields.io/npm/v/@skyeav/tablassist.svg)](https://www.npmjs.com/package/@skyeav/tablassist)
[![License](https://img.shields.io/npm/l/@skyeav/tablassist.svg)](https://github.com/SkyeAv/Tablassist/blob/master/LICENSE)

[OpenCode](https://opencode.ai) plugin for [Tablassert](https://github.com/SkyeAv/Tablassert) table configuration — entity resolution, YAML validation, Biolink documentation, data profiling, document extraction, and PMC discovery tools.

## Installation

```bash
npm install @skyeav/tablassist
```

Requires the [Tablassist CLI](https://pypi.org/project/tablassist/) installed and on `PATH`:

```bash
pip install tablassist
```

## Tools

The plugin exposes 26 CLI commands as OpenCode tools organized into five domains:

### API (`tools/api.ts`)

| Tool | Description |
|---|---|
| `search-curies` | Resolve any non-gene entity by free-text term |
| `search-gene-curies` | Resolve gene CURIEs scoped to an NCBI taxon |
| `resolve-taxon-id` | Look up NCBI Taxon ID from an organism name |
| `download-pmc-tar` | Download and extract a PMC tar archive (first choice) |
| `download-pmc-oa` | Download from PMC OA S3 bucket (fallback) |
| `download-url` | Download an arbitrary URL into an artifact directory |

### Biolink (`tools/biolink.ts`)

| Tool | Description |
|---|---|
| `list-categories` | Enumerate all supported Biolink categories |
| `list-predicates` | Enumerate all supported Biolink predicates |
| `list-qualifiers` | Enumerate all supported Biolink qualifiers |
| `docs-category` | Fetch documentation for a specific category |
| `docs-predicate` | Fetch documentation for a specific predicate |
| `docs-qualifier` | Fetch documentation for a specific qualifier |

### Schema (`tools/schema.ts`)

| Tool | Description |
|---|---|
| `section-schema` | Return the Section Pydantic model as JSON Schema |
| `validate-config-str` | Validate a YAML config from a string |
| `validate-config-file` | Validate a YAML config file on disk |

### Files (`tools/files.ts`)

| Tool | Description |
|---|---|
| `extract-text` | Fast raw text extraction via Textract |
| `extract-text-semantic` | Structured Markdown extraction via Docling |
| `excel-sheets` | List sheet names in an Excel file |
| `preview-excel` | Preview first N rows of an Excel sheet |
| `preview-csv` | Preview first N rows of a CSV/TSV |
| `describe-excel` | Profile an Excel sheet with statistics |
| `describe-csv` | Profile a CSV/TSV with statistics |

### Discovery (`tools/discover.ts`)

| Tool | Description |
|---|---|
| `search-pmc` | Search PubMed Central for open-access articles |
| `get-pmc-summary` | Fetch metadata and supplements for a PMC article |
| `discovery-ledger` | Manage cross-session discovery progress ledger |
| `consolidate-datalake` | Move referenced files into a flat DATALAKE directory |

## Agents

Five agents orchestrate the configuration workflow:

| Agent | Role | Receives system prompt resources |
|---|---|---|
| `the-configurator` | Primary orchestrator; validates configs, delegates to subagents | Yes |
| `the-builder` | YAML construction and validation specialist | Yes |
| `the-extractor` | Data extraction and preview subagent | No |
| `the-pioneer` | Ledger-driven multi-paper discovery workflow | Yes |
| `the-scout` | Lightweight search with minimal context | No |

## Slash Commands

All commands use the `tablassist:` prefix.

- **`/tablassist:audit <config-path>`** — Deep report-first review: validates structure, downloads source data via the extractor fallback chain, inspects tabular data, spot-checks CURIE resolution and Biolink alignment, recommends improvements without applying them
- **`/tablassist:validate <config-path>`** — Structural validation only; fixes schema errors, reports pass/fail
- **`/tablassist:preview <file-path>`** — Profile and preview rows from a CSV, TSV, or Excel file
- **`/tablassist:search <term>`** — Search for CURIE candidates matching a term
- **`/tablassist:discover <topic>`** — Autonomous multi-paper discovery loop with ledger tracking

## Architecture

```
plugin/
├── agents/               # Agent persona definitions (Markdown)
│   ├── the-builder.md
│   ├── the-configurator.md
│   ├── the-extractor.md
│   ├── the-pioneer.md
│   └── the-scout.md
└── src/
    ├── index.ts           # Plugin entry point
    ├── cli.ts             # CLI runner (shell execution wrapper)
    ├── cache.ts           # Parallel resource caching (schema, docs, examples)
    ├── agent-tracker.ts   # Session → agent mapping with resource routing
    ├── hooks/
    │   ├── agent-config.ts       # Agent configuration hook
    │   ├── command-config.ts     # Slash command registration
    │   ├── system-prompt.ts      # Per-agent system prompt injection
    │   ├── temperature.ts        # Model-specific temperature fallbacks
    │   └── yaml-validation.ts    # Post-validation on generated YAML
    └── tools/
        ├── api.ts                # CURIE search, taxon, PMC download tools
        ├── biolink.ts            # Biolink schema enumeration and docs
        ├── schema.ts             # YAML validation tools
        ├── files.ts              # Extraction and data preview tools
        ├── discover.ts           # PMC search and discovery ledger tools
        └── shared.ts             # Shared CLI tool factory
```

### PMC Retrieval Chain

Agents follow a deterministic fallback for PMC content:

1. `download-pmc-tar` (first choice)
2. `download-pmc-oa` (fallback for OA articles)
3. `download-url` / `webfetch` (last resort, only with URLs from real tool responses)

## Development

```bash
bun install              # install dependencies
bun run lint             # lint with Biome
bun run format           # format with Biome
bun x tsc --noEmit       # type check
bun test                 # run all tests
```

## License

[Apache License 2.0](../LICENSE)
