import os
import random
from typing import Any, Union

from cyclopts import App
from tablassert.enums import Categories, Predicates, Qualifiers

from tablassist.utils import get_json_response, get_static_content

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
def get_random_production_table_configuration_example() -> str:
    urls: list[str] = [
        "https://raw.githubusercontent.com/glusman-team/MOKGConfiguration/refs/heads/master/TABLE/MBKG/ALAM1.yaml",
        "https://raw.githubusercontent.com/glusman-team/MOKGConfiguration/refs/heads/master/TABLE/MBKG/AVUTHU1.yaml",
        "https://raw.githubusercontent.com/glusman-team/MOKGConfiguration/refs/heads/master/TABLE/MBKG/AVUTHU2.yaml",
        "https://raw.githubusercontent.com/glusman-team/MOKGConfiguration/refs/heads/master/TABLE/MBKG/BLANTON1.yaml",
        "https://raw.githubusercontent.com/glusman-team/MOKGConfiguration/refs/heads/master/TABLE/MBKG/BOHMAN4.yaml",
    ]
    url: str = urls[random.randint(0, 4)]
    return get_static_content(url)


TABLASSIST_USERNAME: str = os.environ.get("TABLASSIST_USERNAME", "")
TABLASSIST_API_KEY: str = os.environ.get("TABLASSIST_API_KEY", "")


@CLI.commmand
def search_for_curies_with_term(term: str) -> Union[list[Any], dict[str, Any]]:
    url: str = "https//hypatia.systemsbiology.net/configurator-api/search-for-curies"
    params: dict[str, str] = {"username": TABLASSIST_USERNAME, "api-key": TABLASSIST_API_KEY, "term": term}

    return get_json_response(url, params)


@CLI.command
def search_for_gene_curies_in_taxon_with_term(term: str, ncbi_taxon: int = 9606) -> Union[list[Any], dict[str, Any]]:
    url: str = "https//hypatia.systemsbiology.net/configurator-api/search-for-gene-curies-in-ncbi-taxon"
    params: dict[str, str] = {
        "username": TABLASSIST_USERNAME,
        "api-key": TABLASSIST_API_KEY,
        "term": term,
        "taxon": f"{ncbi_taxon}",
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


def serve() -> None:
    CLI()
