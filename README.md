# Tablassist

[![PyPI](https://img.shields.io/pypi/v/tablassist.svg)](https://pypi.org/project/tablassist/)
[![npm](https://img.shields.io/npm/v/@skyeav/tablassist.svg)](https://www.npmjs.com/package/@skyeav/tablassist)
[![Python](https://img.shields.io/pypi/pyversions/tablassist.svg)](https://pypi.org/project/tablassist/)
[![License](https://img.shields.io/pypi/l/tablassist.svg)](https://github.com/SkyeAv/Tablassist/blob/master/LICENSE)

AI-assisted table configuration generation for [Tablassert](https://github.com/SkyeAv/Tablassert) — entity resolution, YAML validation, and Biolink documentation lookup.

Tablassist helps you create and validate Tablassert table configurations. Where Tablassert extracts knowledge assertions from tabular data into NCATS Translator-compliant KGX NDJSON, Tablassist provides the tooling to build those configurations correctly — with CURIE resolution, schema validation, and interactive documentation built in.

## Components

This is a polyglot monorepo with two distributable packages:

| Package | Description | Registry |
|---|---|---|
| [`cli/`](cli/) | Python CLI tool for configuration authoring and validation | [PyPI](https://pypi.org/project/tablassist/) |
| [`plugin/`](plugin/) | OpenCode plugin exposing CLI tools to AI agents | [npm](https://www.npmjs.com/package/@skyeav/tablassist) |

## Quick Start

### CLI

```bash
pip install tablassist
```

```bash
# Validate a table configuration
tablassist validate-config-file config.yaml

# Search for entity CURIEs
tablassist search-curies "breast cancer"

# List supported Biolink categories
tablassist list-categories
```

### OpenCode Plugin

```bash
npm install @skyeav/tablassist
```

Add to your OpenCode configuration to give AI agents access to Tablassert documentation, CURIE search, schema validation, and more.

## Key Features

- **CURIE Resolution** — Search and resolve biological entity identifiers via the Configurator API
- **YAML Validation** — Validate table configurations against the Tablassert schema with detailed error reporting
- **Biolink Documentation** — Fetch documentation for categories, predicates, and qualifiers directly from Biolink
- **Data Preview** — Inspect Excel and CSV files before building configurations
- **Text Extraction** — Extract text from PDFs, DOCX, and other document formats
- **Configuration Examples** — Access production YAML config examples and documentation

## Development

See [`cli/README.md`](cli/README.md) for Python CLI development and [`plugin/README.md`](plugin/README.md) for plugin development.

```bash
# CLI
cd cli
uv sync
uv run ruff check .
uv run pyright
uv run pytest

# Plugin
cd plugin
bun install
bun x tsc --noEmit
bun test
```

## License

[Apache License 2.0](LICENSE)

## Contributors

[Skye Lane Goetz](mailto:sgoetz@isbscience.org) — Institute for Systems Biology, CalPoly SLO
