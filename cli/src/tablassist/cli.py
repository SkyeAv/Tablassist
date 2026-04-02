import os
import re
import subprocess
from pathlib import Path
from typing import Any, Optional, Union

import httpx
import textract
import yaml
from cyclopts import App
from pydantic import ValidationError
from tablassert.enums import Categories, Predicates, Qualifiers
from tablassert.ingests import from_yaml, to_sections
from tablassert.models import Section

from tablassist.utils import get_biolink_html_documentation, get_json_response, get_static_content

CLI: App = App()


@CLI.command
def get_table_configuration_documentation() -> str:
    url: str = "https://raw.githubusercontent.com/SkyeAv/Tablassert/main/docs/configuration/table.md"
    return get_static_content(url)


@CLI.command
def get_advanced_table_configuration_examples_documentation() -> str:
    url: str = "https://raw.githubusercontent.com/SkyeAv/Tablassert/main/docs/configuration/advanced-example.md"
    return get_static_content(url)


@CLI.command
def get_tablassert_cli_tutorial_documentation() -> str:
    url: str = "https://raw.githubusercontent.com/SkyeAv/Tablassert/blob/main/docs/tutorial.md"
    return get_static_content(url)


@CLI.command
def get_production_table_configuration_example_without_sections() -> str:
    url: str = (
        "https://raw.githubusercontent.com/glusman-team/MOKGConfiguration/refs/heads/master/TABLE/MBKG/ALAM1.yaml"
    )
    return get_static_content(url)


@CLI.command
def get_production_table_configuration_example_with_sections() -> str:
    url: str = (
        "https://raw.githubusercontent.com/glusman-team/MOKGConfiguration/refs/heads/master/TABLE/MBKG/BLANTON1.yaml"
    )
    return get_static_content(url)


TABLASSIST_USERNAME: str = os.environ.get("TABLASSIST_USERNAME", "")
TABLASSIST_API_KEY: str = os.environ.get("TABLASSIST_API_KEY", "")


@CLI.command
def search_for_curies_with_term(term: str) -> Union[list[Any], dict[str, Any]]:
    url: str = "https://hypatia.systemsbiology.net/configurator-api/search-for-curies"
    params: dict[str, Any] = {"username": TABLASSIST_USERNAME, "api-key": TABLASSIST_API_KEY, "term": term}

    return get_json_response(url, params)


@CLI.command
def get_cannonical_curie_information_from_curie(curie: str) -> Union[list[Any], dict[str, Any]]:
    url: str = "https://hypatia.systemsbiology.net/get-canonical-curie-info"
    params: dict[str, Any] = {"username": TABLASSIST_USERNAME, "api-key": TABLASSIST_API_KEY, "curie": curie}

    return get_json_response(url, params)


@CLI.command
def download_and_extract_pmc_tarbell(pmc_id: int, dest_dir: Path = Path(".")) -> dict[str, Any]:
    url: str = "https://hypatia.systemsbiology.net/get-canonical-curie-info"

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
def search_for_gene_curies_in_taxon_with_term(term: str, ncbi_taxon: int = 9606) -> Union[list[Any], dict[str, Any]]:
    url: str = "https://hypatia.systemsbiology.net/configurator-api/search-for-gene-curies-in-ncbi-taxon"
    params: dict[str, Any] = {
        "username": TABLASSIST_USERNAME,
        "api-key": TABLASSIST_API_KEY,
        "term": term,
        "taxon": ncbi_taxon,
    }

    return get_json_response(url, params)


@CLI.command
def get_ncbi_taxon_id_from_organism_name(organism_name: str) -> Union[list[Any], dict[str, Any]]:
    url: str = "https://hypatia.systemsbiology.net/get-ncbi-taxon-id-from-organism-name"
    params: dict[str, Any] = {
        "username": TABLASSIST_USERNAME,
        "api-key": TABLASSIST_API_KEY,
        "organism-name": organism_name,
    }

    return get_json_response(url, params)


@CLI.command
def get_supported_biolink_categories() -> list[str]:
    return [x.value for x in Categories]


@CLI.command
def get_supported_biolink_predicates() -> list[str]:
    return [x.value for x in Predicates]


@CLI.command
def get_supported_biolink_qualifiers() -> list[str]:
    return [x.value for x in Qualifiers]


@CLI.command
def get_section_pydantic_schema_as_json() -> str:
    return Section.model_json_schema()


@CLI.command
def validate_full_yaml_table_configuration(yaml_file: Path) -> Union[dict[str, Any], list[dict[str, Any]]]:
    try:
        raw: Any = from_yaml(yaml_file)
    except yaml.scanner.ScannerError as e:  # pyright: ignore
        return {"error": f"YAML Syntax error at line {e.problem_mark.line + 1}: {e.problem}"}
    except yaml.parser.ParserError as e:  # pyright: ignore
        return {"error": f"YAML Parser error: {e}"}
    except yaml.YAMLError as e:
        return {"error": f"YAML error: {e}"}

    sections: list[dict[str, Any]] = to_sections(raw)

    errors: list[dict[str, Any]] = []
    for idx, s in enumerate(sections, start=1):
        try:
            Section.model_validate(s)
            errors += [{"section-number": idx, "section": s, "status": "ok"}]
        except ValidationError as e:
            errors += [{"section-number": idx, "section": s, "error": f"{e}"}]

    return errors


@CLI.command
def get_specific_biolink_category_documentation(catergory: str) -> str:
    return get_biolink_html_documentation(catergory) or f"ERROR | {catergory} is not a supported biolink catergory"


@CLI.command
def get_specific_biolink_predicate_documentation(predicate: str) -> str:
    return get_biolink_html_documentation(predicate) or f"ERROR | {predicate} is not a supported biolink predicate"


@CLI.command
def get_specific_biolink_qualifier_documentation(qualifier: str) -> str:
    return get_biolink_html_documentation(qualifier) or f"ERROR | {qualifier} is not a supported biolink qualifier"


@CLI.command
def extract_text_from_diverse_file_types_with_textract(file: Path, extension: Optional[str] = None) -> str:
    if file.suffix == "pdf":
        return textract.process(file, method="pdfminer")
    elif extension:
        return textract.process(file, extension=extension)
    else:
        return textract.process(file)


def serve() -> None:
    CLI()
