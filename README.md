# Tablassist

[![PyPI](https://img.shields.io/pypi/v/tablassist.svg)](https://pypi.org/project/tablassist/)
[![npm](https://img.shields.io/npm/v/@skyeav/tablassist.svg)](https://www.npmjs.com/package/@skyeav/tablassist)
[![Python](https://img.shields.io/pypi/pyversions/tablassist.svg)](https://pypi.org/project/tablassist/)
[![License](https://img.shields.io/pypi/l/tablassist.svg)](https://github.com/SkyeAv/Tablassist/blob/master/LICENSE)

AI-assisted configuration generation for [Tablassert](https://github.com/SkyeAv/Tablassert) — entity resolution, YAML validation, Biolink documentation, and PMC literature discovery.

Tablassert extracts knowledge assertions from tabular data into NCATS Translator-compliant KGX NDJSON. Tablassist provides the tooling to build those configurations correctly — with CURIE resolution, schema validation, document extraction, data profiling, and PMC integration built in.

## Components

Polyglot monorepo with two distributable packages:

| Package | Description | Registry |
|---|---|---|
| [`cli/`](cli/) | Python CLI for configuration authoring and validation | [PyPI](https://pypi.org/project/tablassist/) |
| [`plugin/`](plugin/) | OpenCode plugin exposing CLI tools to AI agents | [npm](https://www.npmjs.com/package/@skyeav/tablassist) |

## Quick Start

### CLI

```bash
pip install tablassist
```

```bash
tablassist validate-config-file config.yaml
tablassist search-curies "breast cancer"
tablassist list-categories
```

### OpenCode Plugin

```bash
npm install @skyeav/tablassist
```

Add to your OpenCode configuration to give AI agents access to CURIE search, schema validation, Biolink docs, PMC discovery, and more.

## Features

- **Entity Resolution** — Search and resolve biological entity identifiers via the Configurator API (`search-curies`, `search-gene-curies`, `resolve-taxon-id`)
- **Biolink Schema** — Enumerate and fetch documentation for categories, predicates, and qualifiers from the Biolink model
- **YAML Validation** — Validate configurations against the Tablassert Pydantic schema with detailed per-section error reporting
- **Data Profiling** — Inspect Excel and CSV files with schema inference, per-column statistics, and sample rows (`describe-excel`, `describe-csv`, `preview-excel`, `preview-csv`)
- **Document Extraction** — Fast raw text via Textract (`extract-text`) or structured Markdown via Docling (`extract-text-semantic`) with OCR control
- **PMC Integration** — Search PubMed Central, fetch article metadata, and download archives (`search-pmc`, `get-pmc-summary`, `download-pmc-tar`, `download-pmc-oa`)
- **Discovery Workflow** — Ledger-driven multi-paper pipeline with concurrent claim coordination, DATALAKE consolidation, and cross-session state (`discovery-ledger`, `consolidate-datalake`)

## Development

See [`cli/README.md`](cli/README.md) and [`plugin/README.md`](plugin/README.md) for package-specific details.

```bash
# CLI
cd cli
uv sync
uv run ruff check . && uv run ruff format .
uv run pyright
uv run --group dev python -m pytest

# Plugin
cd plugin
bun install
bun run lint && bun run format
bun x tsc --noEmit
bun test
```

Pre-commit hooks (via [`prek.toml`](prek.toml)) run all checks automatically on `git commit`.

## License

[Apache License 2.0](LICENSE)

## Contributors

[Skye Lane Goetz](mailto:sgoetz@isbscience.org) — Institute for Systems Biology, CalPoly SLO
