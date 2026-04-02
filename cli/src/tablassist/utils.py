from typing import Any, Optional, Union
from urllib.parse import quote

import httpx
import trafilatura


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
