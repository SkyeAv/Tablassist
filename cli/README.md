# Tablassist CLI

[![PyPI](https://img.shields.io/pypi/v/tablassist.svg)](https://pypi.org/project/tablassist/)
[![Python](https://img.shields.io/pypi/pyversions/tablassist.svg)](https://pypi.org/project/tablassist/)
[![License](https://img.shields.io/pypi/l/tablassist.svg)](https://github.com/SkyeAv/Tablassist/blob/master/LICENSE)

Python CLI tool for AI-assisted [Tablassert](https://github.com/SkyeAv/Tablassert) table configuration generation — entity resolution, YAML validation, and Biolink documentation lookup.

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
```

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
uv run pytest                        # run all tests
```

## License

[Apache License 2.0](../LICENSE)
