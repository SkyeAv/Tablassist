# @skyeav/tablassist

[![npm](https://img.shields.io/npm/v/@skyeav/tablassist.svg)](https://www.npmjs.com/package/@skyeav/tablassist)
[![License](https://img.shields.io/npm/l/@skyeav/tablassist.svg)](https://github.com/SkyeAv/Tablassist/blob/master/LICENSE)

[OpenCode](https://opencode.ai) plugin for [Tablassert](https://github.com/SkyeAv/Tablassert) table configuration — entity resolution, YAML validation, and Biolink documentation tools.

## Installation

```bash
npm install @skyeav/tablassist
```

Add the plugin to your OpenCode configuration. The plugin requires the Tablassist CLI to be installed and available on `PATH`:

```bash
pip install tablassist
```

Current Tablassist CLI releases include Docling in the base install, so the plugin can call `extract-text-semantic` without any separate semantic extraction helper.

## What It Does

This plugin gives AI agents access to the full Tablassist CLI toolset through OpenCode:

- **Entity Resolution** — Search and resolve biological CURIEs (genes, diseases, chemicals)
- **YAML Validation** — Validate Tablassert table configurations with detailed error reporting
- **Config Audit** — Run deep, report-first reviews of existing configs before semantic edits
- **Biolink Documentation** — Look up categories, predicates, and qualifiers from the Biolink model
- **Data Preview** — Inspect Excel and CSV files before building configurations
- **Dual Text Extraction** — Use fast raw Textract extraction or richer semantic Docling extraction depending on the source
- **Configuration Reference** — Access production examples and schema documentation

Full config validation expects `template:` as the top-level YAML key, with optional `sections:`. The standalone `validate-section-str` tool is only for checking an individual merged section shape.

Document extraction tools:

- `extract-text` for fast raw text extraction from PDFs, DOCX, and similar files
- `extract-text-semantic` for richer Markdown or plain-text extraction with `ocr=auto` by default

The semantic extractor calls the CLI's built-in Docling path directly, so the plugin exposes the same semantic extraction endpoint that the CLI ships by default.

## Architecture

The plugin wraps the [Tablassist CLI](../cli/) and exposes its commands as OpenCode tools:

```
plugin/
├── src/
│   ├── index.ts          # Plugin entry point
│   ├── cli.ts            # CLI runner and shell execution
│   ├── cache.ts          # Resource caching system
│   ├── hooks/            # System prompt and YAML validation hooks
│   └── tools/            # Tool definitions (API, Biolink, files, schema)
└── agents/               # Agent definitions (configurator, extractor, builder)
```

Three agents orchestrate the configuration workflow:

| Agent | Role |
|---|---|
| `the-configurator` | Primary orchestrator for building table configs |
| `the-extractor` | Subagent for data extraction and preview |
| `the-builder` | Subagent for YAML construction and validation |

## Slash Commands

- `/audit <config-path>` performs a deep, report-first review: validates structure, inspects source and publication context, and recommends semantic improvements without applying them until you approve.
- `/validate <config-path>` validates a config file and reports schema errors.
- `/preview <file-path>` previews rows from a CSV, TSV, or Excel file.
- `/search <term>` searches for CURIE candidates matching a term.

Example:

```bash
/audit ./configs/example.yaml
```

## Development

```bash
bun install                          # install dependencies
bun run ./src/index.ts               # run
bun x tsc --noEmit                   # type check
bun test                             # run all tests
```

## License

[Apache License 2.0](../LICENSE)
