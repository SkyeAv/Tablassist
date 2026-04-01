from typing import Any, Optional, Union

import httpx


def get_static_content(url: str) -> str:
    r: Any = httpx.get(url)
    return r.text


def get_json_response(url: str, params: Optional[dict[str, Any]] = None) -> Union[list[Any], dict[str, Any]]:
    if params:
        r: Any = httpx.get(url, params=params)
    else:
        r = httpx.get(url)

    return r.json()
