import random

from cyclopts import App
from tablassert.enums import Categories, Predicates, Qualifiers

from tablassist.utils import get_static_content

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
