import os
import re
import subprocess
from pathlib import Path
from typing import Any, Literal, Optional, Union

import fastexcel
import httpx
import polars as pl
import textract
import yaml
from cyclopts import App
from tablassert.enums import Categories, Predicates, Qualifiers
from tablassert.ingests import from_yaml
from tablassert.models import Section

from tablassist.utils import (
    get_biolink_html_documentation,
    get_json_response,
    get_static_content,
    parse_yaml_string,
    validate_section,
)

CLI: App = App()


@CLI.command
def docs_table_config() -> str:
    """Fetch Tablassert table configuration spec documentation."""
    url: str = "https://raw.githubusercontent.com/SkyeAv/Tablassert/main/docs/configuration/table.md"
    return get_static_content(url)


@CLI.command
def docs_advanced_examples() -> str:
    """Fetch advanced table configuration examples documentation."""
    url: str = "https://raw.githubusercontent.com/SkyeAv/Tablassert/main/docs/configuration/advanced-example.md"
    return get_static_content(url)


@CLI.command
def docs_tutorial() -> str:
    """Fetch Tablassert CLI tutorial documentation."""
    url: str = "https://raw.githubusercontent.com/SkyeAv/Tablassert/blob/main/docs/tutorial.md"
    return get_static_content(url)


@CLI.command
def example_no_sections() -> str:
    """Fetch a production YAML config example without sections."""
    url: str = (
        "https://raw.githubusercontent.com/glusman-team/MOKGConfiguration/refs/heads/master/TABLE/MBKG/ALAM1.yaml"
    )
    return get_static_content(url)


@CLI.command
def example_with_sections() -> str:
    """Fetch a production YAML config example with sections."""
    url: str = (
        "https://raw.githubusercontent.com/glusman-team/MOKGConfiguration/refs/heads/master/TABLE/MBKG/BLANTON1.yaml"
    )
    return get_static_content(url)


TABLASSIST_USERNAME: str = os.environ.get("TABLASSIST_USERNAME", "")
TABLASSIST_API_KEY: str = os.environ.get("TABLASSIST_API_KEY", "")


@CLI.command
def search_curies(term: str) -> Union[list[Any], dict[str, Any]]:
    """Search CURIE candidates by term via Configurator API."""
    url: str = "https://hypatia.systemsbiology.net/configurator-api/search-for-curies"
    params: dict[str, Any] = {"username": TABLASSIST_USERNAME, "api-key": TABLASSIST_API_KEY, "term": term}

    return get_json_response(url, params)


@CLI.command
def get_curie_info(curie: str) -> Union[list[Any], dict[str, Any]]:
    """Resolve a single canonical CURIE record."""
    url: str = "https://hypatia.systemsbiology.net/configurator-api/get-canonical-curie-info"
    params: dict[str, Any] = {"username": TABLASSIST_USERNAME, "api-key": TABLASSIST_API_KEY, "curie": curie}

    return get_json_response(url, params)


@CLI.command
def download_pmc_tar(pmc_id: int, dest_dir: Path = Path(".")) -> dict[str, Any]:
    """Download and extract a PMC tar archive by PMC ID."""
    url: str = "https://hypatia.systemsbiology.net/configurator-api/download-from-pmc-tars"

    params: dict[str, Any] = {"username": TABLASSIST_USERNAME, "api-key": TABLASSIST_API_KEY, "pmc-id": pmc_id}

    with httpx.stream("GET", url, params=params) as r:
        if r.status_code == 404:
            error: dict[str, Any] = r.json()
            return error

        d: str = r.headers["content-disposition"]
        matches: object = re.search(r"filename=(.+)", d)

        filename: str = matches.group(1) if matches else "download.tar.xz"
        p: Path = dest_dir / filename
        with p.open("wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)

    cmd: list[str] = ["tar", "-xvf", f"{p}", "&&", "ls", "-lh", f"{dest_dir}"]
    r: Any = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    return {"status": "ok", "stdout": r.stdout, "stderr": r.stderr}


@CLI.command
def search_gene_curies(term: str, ncbi_taxon: int = 9606) -> Union[list[Any], dict[str, Any]]:
    """Search gene CURIE candidates by term within an NCBI taxon."""
    url: str = "https://hypatia.systemsbiology.net/configurator-api/search-for-gene-curies-in-ncbi-taxon"
    params: dict[str, Any] = {
        "username": TABLASSIST_USERNAME,
        "api-key": TABLASSIST_API_KEY,
        "term": term,
        "ncbi-taxon-id": ncbi_taxon,
    }

    return get_json_response(url, params)


@CLI.command
def resolve_taxon_id(organism_name: str) -> Union[list[Any], dict[str, Any]]:
    """Resolve an NCBI Taxon ID from an organism name."""
    url: str = "https://hypatia.systemsbiology.net/configurator-api/get-ncbi-taxon-id-from-organism-name"
    params: dict[str, Any] = {
        "username": TABLASSIST_USERNAME,
        "api-key": TABLASSIST_API_KEY,
        "organism-name": organism_name,
    }

    return get_json_response(url, params)


@CLI.command
def list_categories() -> list[str]:
    """List all supported Biolink categories."""
    return [x.value for x in Categories]


@CLI.command
def list_predicates() -> list[str]:
    """List all supported Biolink predicates."""
    return [x.value for x in Predicates]


@CLI.command
def list_qualifiers() -> list[str]:
    """List all supported Biolink qualifiers."""
    return [x.value for x in Qualifiers]


@CLI.command
def section_schema() -> dict[str, Any]:
    """Return the Section Pydantic model as JSON schema."""
    return Section.model_json_schema()


@CLI.command
def validate_section_str(yaml_string: str) -> dict[str, Any]:
    """Validate a single YAML table configuration section from a string."""
    raw: Any = parse_yaml_string(yaml_string)
    if isinstance(raw, dict) and "error" in raw:
        return raw

    return validate_section(raw)


@CLI.command
def validate_config_str(yaml_string: str) -> Union[dict[str, Any], list[dict[str, Any]]]:
    """Validate a full YAML table configuration from a string."""
    raw: Any = parse_yaml_string(yaml_string)
    if isinstance(raw, dict) and "error" in raw:
        return raw

    sections: list[dict[str, Any]] = raw if isinstance(raw, list) else [raw]

    errors: list[dict[str, Any]] = []
    for s in sections:
        errors += [validate_section(s)]

    return errors


@CLI.command
def validate_config_file(yaml_file: Path) -> Union[dict[str, Any], list[dict[str, Any]]]:
    """Validate a full YAML table configuration from a file path."""
    try:
        raw: Any = from_yaml(yaml_file)
    except yaml.scanner.ScannerError as e:  # pyright: ignore
        return {"error": f"YAML Syntax error at line {e.problem_mark.line + 1}: {e.problem}"}
    except yaml.parser.ParserError as e:  # pyright: ignore
        return {"error": f"YAML Parser error: {e}"}
    except yaml.YAMLError as e:
        return {"error": f"YAML error: {e}"}

    sections: list[dict[str, Any]] = raw if isinstance(raw, list) else [raw]

    errors: list[dict[str, Any]] = []
    for s in sections:
        errors += [validate_section(s)]

    return errors


@CLI.command
def docs_category(category: str) -> str:
    """Fetch Biolink documentation for a specific category."""
    return get_biolink_html_documentation(category) or f"ERROR | {category} is not a supported biolink category"


@CLI.command
def docs_predicate(predicate: str) -> str:
    """Fetch Biolink documentation for a specific predicate."""
    return get_biolink_html_documentation(predicate) or f"ERROR | {predicate} is not a supported biolink predicate"


@CLI.command
def docs_qualifier(qualifier: str) -> str:
    """Fetch Biolink documentation for a specific qualifier."""
    return get_biolink_html_documentation(qualifier) or f"ERROR | {qualifier} is not a supported biolink qualifier"


@CLI.command
def extract_text(file: Path, extension: Optional[str] = None) -> str:
    """Extract text from a file using textract (PDF, DOCX, etc.)."""
    if file.suffix == "pdf":
        return textract.process(file, method="pdfminer")
    elif extension:
        return textract.process(file, extension=extension)
    else:
        return textract.process(file)


@CLI.command
def excel_sheets(file: Path) -> list[str]:
    """List sheet names in an Excel spreadsheet."""
    wb: Any = fastexcel.read_excel(file)
    return wb.sheet_names


@CLI.command
def preview_excel(
    file: Path, sheet_name: str, n_rows: int, engine: Literal["calamine", "openpyxl", "xlsx2csv"] = "calamine"
) -> dict[str, Any]:
    """Preview the first N rows of an Excel sheet as a dict."""
    df: pl.DataFrame = pl.read_excel(source=file, sheet_name=sheet_name, engine=engine, infer_schema_length=None)
    df = df.head(n_rows)
    return df.to_dict(as_series=False)


@CLI.command
def preview_csv(file: Path, n_rows: int, separator: str = ",") -> dict[str, Any]:
    """Preview the first N rows of a CSV/tabular file as a dict."""
    df: pl.DataFrame = pl.read_csv(source=file, n_rows=n_rows, separator=separator)
    return df.to_dict(as_series=False)


def serve() -> None:
    CLI()
