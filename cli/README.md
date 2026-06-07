# Tablassist CLI

[![PyPI](https://img.shields.io/pypi/v/tablassist.svg)](https://pypi.org/project/tablassist/)
[![Python](https://img.shields.io/pypi/pyversions/tablassist.svg)](https://pypi.org/project/tablassist/)
[![License](https://img.shields.io/pypi/l/tablassist.svg)](https://github.com/SkyeAv/Tablassist/blob/master/LICENSE)

Python CLI for AI-assisted [Tablassert](https://github.com/SkyeAv/Tablassert) configuration generation — entity resolution, YAML validation, Biolink documentation, data profiling, document extraction, and PMC integration.

## Installation

```bash
pip install tablassist
```

For CPUs without required SIMD instructions:

```bash
pip install "tablassist[rtcompat]"
```

### Requirements

- Python >= 3.13
- `TABLASSIST_USERNAME` and `TABLASSIST_API_KEY` environment variables for API-accessing commands
- `aws` CLI in PATH for `download-pmc-oa`

## Commands

### Entity Resolution

```bash
tablassist search-curies "breast cancer"
tablassist search-gene-curies "BRCA1" --ncbi-taxon 9606
tablassist resolve-taxon-id "Homo sapiens"
```

### Biolink Reference

```bash
tablassist list-categories
tablassist list-predicates
tablassist list-qualifiers
tablassist docs-category "Gene"
tablassist docs-predicate "interacts_with"
tablassist docs-qualifier "qualified_predicate"
```

### Configuration Reference

```bash
tablassist docs-table-config
tablassist section-schema
```

### YAML Validation

Full config files use `template:` as the top-level key with optional `sections:`. Use `validate-section-str` only for individual section mappings.

```bash
tablassist validate-config-file config.yaml
tablassist validate-config-str '<yaml>'
tablassist validate-section-str '<yaml>'
```

### Data Profiling

```bash
tablassist describe-excel data.xlsx "Sheet1"
tablassist describe-csv data.csv
tablassist excel-sheets data.xlsx
tablassist preview-excel data.xlsx "Sheet1" 10
tablassist preview-csv data.csv 10 --separator ","
```

`describe-*` provides schema, sample rows, per-column dtypes, null/unique counts, and statistics. Prefer for first-pass inspection. `preview-*` returns raw `{column: [values]}` dicts for narrow follow-up.

### Document Extraction

```bash
tablassist extract-text document.pdf
tablassist extract-text-semantic document.pdf
tablassist extract-text-semantic document.pdf text off
```

| Command | Engine | Output | Best for |
|---|---|---|---|
| `extract-text` | Textract | Raw text | Fast bulk extraction where layout doesn't matter |
| `extract-text-semantic` | Docling | Markdown or text | Preserving headings, tables, reading order |

`extract-text-semantic` arguments: `file`, `output_format` (`markdown` \| `text`, default `markdown`), `ocr` (`auto` \| `off` \| `on`, default `auto`).

### PMC Integration

```bash
tablassist search-pmc "drug repurposing" --max-results 10
tablassist get-pmc-summary 12345
tablassist download-pmc-tar 12345 --dest-dir ./output
tablassist download-pmc-oa 12345 --dest-dir ./output
tablassist download-url https://example.com/file.csv --dest-dir ./output
```

PMC retrieval chain: prefer `download-pmc-tar`, then `download-pmc-oa`, then `download-url` as fallback.

### Discovery Workflow

```bash
tablassist consolidate-datalake config1.yaml config2.yaml --pmc-id 12345 --artifact-root ./data
tablassist discovery-ledger read --ledger-path .ledger/topic/ledger.json --topic "my topic"
tablassist discovery-ledger add --ledger-path .ledger/topic/ledger.json --pmc-id 12345 --status done --topic "my topic"
```

`consolidate-datalake` moves files referenced by `source.local` into a flat `DATALAKE/` directory, rewrites paths, and re-validates configs. `discovery-ledger` manages cross-session progress tracking with actions: `read`, `add`, `check`, `claim`, `release`.

## Development

```bash
uv sync                              # install dependencies
uv run ruff check .                  # lint
uv run ruff check --fix .            # lint with auto-fix
uv run ruff format .                 # format
uv run pyright                       # type check
uv run --group dev python -m pytest  # run all tests
```

## License

[Apache License 2.0](../LICENSE)
