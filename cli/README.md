# Tablassist CLI

[![PyPI](https://img.shields.io/pypi/v/tablassist.svg)](https://pypi.org/project/tablassist/)
[![Python](https://img.shields.io/pypi/pyversions/tablassist.svg)](https://pypi.org/project/tablassist/)
[![License](https://img.shields.io/pypi/l/tablassist.svg)](https://github.com/SkyeAv/Tablassist/blob/master/LICENSE)

Python CLI tool for AI-assisted [Tablassert](https://github.com/SkyeAv/Tablassert) table configuration generation — entity resolution, YAML validation, and Biolink documentation lookup.

Tablassist ships with two document extraction modes:

- `extract-text` for fast raw extraction via Textract
- `extract-text-semantic` for richer Docling-backed semantic extraction with Markdown output and `ocr=auto` by default

## Installation

```bash
pip install tablassist
```

An optional extra is available for CPU compatibility:

```bash
pip install "tablassist[rtcompat]"  # Polars build for CPUs without required instructions
```

### Requirements

- Python >= 3.13
- Environment variables `TABLASSIST_USERNAME` and `TABLASSIST_API_KEY` for API-accessing commands

## Usage

```bash
# Fetch table configuration documentation
tablassist docs-table-config

# Fetch advanced configuration examples
tablassist docs-advanced-examples

# Fetch the CLI tutorial
tablassist docs-tutorial
```

### Entity Resolution

```bash
# Search for entity CURIEs by term
tablassist search-curies "breast cancer"

# Get canonical info for a specific CURIE
tablassist get-curie-info "MONDO:0007254"

# Search gene CURIEs within an NCBI taxon
tablassist search-gene-curies "BRCA1" --ncbi-taxon 9606

# Resolve an NCBI Taxon ID from an organism name
tablassist resolve-taxon-id "Homo sapiens"
```

### Biolink Reference

```bash
# List all supported categories, predicates, or qualifiers
tablassist list-categories
tablassist list-predicates
tablassist list-qualifiers

# Fetch documentation for a specific Biolink element
tablassist docs-category "Gene"
tablassist docs-predicate "interacts_with"
tablassist docs-qualifier "qualified_predicate"
```

### YAML Validation

Full config validation requires `template:` as the top-level key, with optional `sections:`. Use `validate-section-str` only for individual section mappings, not for whole config files.

```bash
# Validate a full config file
tablassist validate-config-file config.yaml

# Validate a single section from a YAML string
tablassist validate-section-str '<yaml>'

# Validate a full config from a YAML string
tablassist validate-config-str '<yaml>'

# Get the Section JSON schema
tablassist section-schema
```

### Data Preview

```bash
# List sheets in an Excel file
tablassist excel-sheets data.xlsx

# Preview rows from an Excel sheet
tablassist preview-excel data.xlsx "Sheet1" 10

# Preview rows from a CSV file
tablassist preview-csv data.csv 10

# Extract text from a document (PDF, DOCX, etc.)
tablassist extract-text document.pdf

# Extract semantic Markdown from a document with Docling
tablassist extract-text-semantic document.pdf

# Extract plain text and explicitly disable OCR
tablassist extract-text-semantic document.pdf text off
```

`extract-text` is optimized for fast, low-overhead text grabs.

`extract-text-semantic` runs IBM Docling in an isolated `uv run` script environment so Tablassist can offer richer extraction without introducing a dependency conflict into the main CLI environment. It is the better choice when reading order, headings, lists, or table-aware Markdown matter more than raw speed.

Arguments for `extract-text-semantic`:

- `file` — local document path
- `output_format` — `markdown` (default) or `text`
- `ocr` — `auto` (default), `off`, or `on`

Use `ocr=auto` for the default balance. Use `ocr=on` for scans and image-heavy PDFs, and `ocr=off` when you know the source is born-digital and want the lightest path.

### PMC Archive Download

```bash
# Download and extract a PMC tar archive
tablassist download-pmc-tar 12345 --dest-dir ./output
```

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
