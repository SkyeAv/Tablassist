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
