from typing import Any, Optional, Union
from urllib.parse import quote

import httpx
import trafilatura
import yaml
from pydantic import ValidationError
from tablassert.models import Section
from yaml import CLoader


def get_static_content(url: str) -> str:
    r: Any = httpx.get(url)
    return r.text


def get_json_response(url: str, params: Optional[dict[str, Any]] = None) -> Union[list[Any], dict[str, Any]]:
    if params:
        r: Any = httpx.get(url, params=params)
    else:
        r = httpx.get(url)

    return r.json()


def get_biolink_html_documentation(biolink_thing: str) -> str:
    url: str = f"https://raw.githubusercontent.com/biolink/biolink-model/gh-pages/{quote(biolink_thing)}/index.html"
    html: str = get_static_content(url)

    return trafilatura.extract(html, output_format="markdown")


def validate_section(s: dict[str, Any]) -> dict[str, Any]:
    try:
        Section.model_validate(s)
        return {"section": s, "status": "ok"}
    except ValidationError as e:
        return {"section": s, "error": f"{e}"}


def parse_yaml_string(yaml_string: str) -> Any:
    try:
        return yaml.load(yaml_string, Loader=CLoader)
    except yaml.scanner.ScannerError as e:  # pyright: ignore
        return {"error": f"YAML Syntax error at line {e.problem_mark.line + 1}: {e.problem}"}
    except yaml.parser.ParserError as e:  # pyright: ignore
        return {"error": f"YAML Parser error: {e}"}
    except yaml.YAMLError as e:
        return {"error": f"YAML error: {e}"}
