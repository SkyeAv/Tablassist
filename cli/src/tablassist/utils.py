import datetime as dt
import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Optional, Union
from urllib.parse import quote

import httpx
import lazy_loader as Lazy
import trafilatura
import yaml
from pydantic import ValidationError
from tablassert.models import Section
from yaml import CLoader

if TYPE_CHECKING:
    import docling
else:
    docling = Lazy.load("docling")

TIMEOUT: float = 60.0  # seconds

NCBI_API_KEY: str = os.environ.get("NCBI_API_KEY", "")

PMC_ESEARCH_URL: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PMC_ESUMMARY_URL: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
PMC_EFETCH_URL: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

XLINK_HREF: str = "{http://www.w3.org/1999/xlink}href"


def get_static_content(url: str) -> str:
    r: Any = httpx.get(url, timeout=TIMEOUT)
    return r.text


def get_json_response(url: str, params: Optional[dict[str, Any]] = None) -> Union[list[Any], dict[str, Any]]:
    if params:
        r: Any = httpx.get(url, params=params, timeout=TIMEOUT)
    else:
        r = httpx.get(url, timeout=TIMEOUT)

    return r.json()


def with_ncbi_api_key(params: dict[str, Any]) -> dict[str, Any]:
    if NCBI_API_KEY:
        return {**params, "api_key": NCBI_API_KEY}
    return params


def get_xml_response(url: str, params: Optional[dict[str, Any]] = None) -> ET.Element:
    text: str = get_static_content(url) if not params else httpx.get(url, params=params, timeout=TIMEOUT).text
    return ET.fromstring(text)


def parse_pmc_supplements(xml_root: ET.Element) -> list[dict[str, str]]:
    supplements: list[dict[str, str]] = []
    for sup in xml_root.iter("supplementary-material"):
        for media in sup.iter("media"):
            href: str = media.get(XLINK_HREF) or media.get("href") or ""
            media_type: str = media.get("mimetype") or media.get("mime-subtype") or ""
            if href:
                supplements.append({"filename": href, "media_type": media_type})
        for inline in sup.iter("inline-supplementary-material"):
            href = inline.get(XLINK_HREF) or inline.get("href") or ""
            if href:
                supplements.append({"filename": href, "media_type": ""})
    return supplements


def parse_pmc_paper_summary(pmc_id: str, item: dict[str, Any]) -> dict[str, Any]:
    authors: list[str] = [a.get("name", "") for a in item.get("authors", []) or [] if a.get("name")]
    has_suppl: bool = any("suppl" in (a.get("name", "") or "").lower() for a in item.get("articleids", []) or [])

    return {
        "pmcid": int(pmc_id),
        "title": item.get("title", ""),
        "authors": authors,
        "date": item.get("pubdate", ""),
        "has_suppl_data": has_suppl,
    }


def parse_pmc_article_xml(pmc_id: int, root: ET.Element) -> dict[str, Any]:
    title_el: Any = next(iter(root.iter("article-title")), None)
    abstract_el: Any = next(iter(root.iter("abstract")), None)

    authors: list[str] = []
    for contrib in root.iter("contrib"):
        role: Optional[str] = contrib.get("contrib-type")
        if role and role != "author":
            continue
        surname_el: Any = next(iter(contrib.iter("surname")), None)
        given_el: Any = next(iter(contrib.iter("given-names")), None)
        surname: str = surname_el.text.strip() if surname_el is not None and surname_el.text else ""
        given: str = given_el.text.strip() if given_el is not None and given_el.text else ""
        name: str = f"{given} {surname}".strip()
        if name:
            authors.append(name)

    return {
        "pmcid": pmc_id,
        "title": "".join(title_el.itertext()).strip() if title_el is not None else "",
        "abstract": "".join(abstract_el.itertext()).strip() if abstract_el is not None else "",
        "authors": authors,
        "supplements": parse_pmc_supplements(root),
    }


def load_ledger(ledger_path: Path, topic: Optional[str]) -> Union[dict[str, Any], None]:
    if not ledger_path.exists():
        return {"topic": topic or "", "entries": []}
    try:
        return json.loads(ledger_path.read_text())
    except json.JSONDecodeError as e:
        return {"error": f"Ledger JSON parse error: {e}"}


def write_ledger(ledger_path: Path, ledger: dict[str, Any]) -> None:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(json.dumps(ledger, indent=2))


def ledger_check(ledger: dict[str, Any], pmc_id: int) -> dict[str, Any]:
    for entry in ledger.get("entries", []):
        if int(entry.get("pmcid", -1)) == int(pmc_id):
            return {"exists": True, "entry": entry}
    return {"exists": False, "entry": None}


def ledger_add(
    ledger_path: Path,
    ledger: dict[str, Any],
    pmc_id: int,
    status: str,
    summary: Optional[str],
    topic: Optional[str],
    config_path: Optional[str],
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "pmcid": int(pmc_id),
        "status": status,
        "summary": summary or "",
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    if config_path:
        entry["config_path"] = config_path
    ledger.setdefault("entries", []).append(entry)
    if topic and not ledger.get("topic"):
        ledger["topic"] = topic
    write_ledger(ledger_path, ledger)
    return {"added": entry, "total_entries": len(ledger["entries"])}


def get_html_as_markdown(url: str) -> str:
    html: str = get_static_content(url)
    return trafilatura.extract(html, output_format="markdown") or ""


def get_biolink_html_documentation(biolink_thing: str) -> str:
    url: str = f"https://raw.githubusercontent.com/biolink/biolink-model/gh-pages/{quote(biolink_thing)}/index.html"
    return get_html_as_markdown(url)


def validate_section(s: dict[str, Any]) -> dict[str, Any]:
    section: dict[str, Any] = {k: v for k, v in s.items() if k != "config"}

    try:
        Section.model_validate(section)
        return {"section": section, "status": "ok"}
    except ValidationError as e:
        return {"section": section, "error": f"{e}"}


def validate_config_root(raw: Any) -> Optional[dict[str, Any]]:
    if not isinstance(raw, dict):
        return {"error": "Full YAML configs must be mappings with top-level template and optional sections keys."}

    if "template" not in raw and "sections" not in raw:
        return {
            "error": (
                "Full YAML configs must include `template:` as a top-level key, with optional `sections:`. "
                "Bare section mappings are only valid with `validate_section_str`; wrap them under `template:` "
                "before using full-config validation."
            )
        }

    return None


def parse_yaml_string(yaml_string: str) -> Any:
    try:
        return yaml.load(yaml_string, Loader=CLoader)
    except yaml.scanner.ScannerError as e:  # pyright: ignore
        return {"error": f"YAML Syntax error at line {e.problem_mark.line + 1}: {e.problem}"}
    except yaml.parser.ParserError as e:  # pyright: ignore
        return {"error": f"YAML Parser error: {e}"}
    except yaml.YAMLError as e:
        return {"error": f"YAML error: {e}"}


def build_semantic_converter(ocr: Literal["auto", "off", "on"] = "auto") -> Any:
    """Build a Docling converter for semantic extraction."""
    if ocr == "auto":
        return docling.document_converter.DocumentConverter()  # pyright: ignore

    pipeline_options = docling.datamodel.pipeline_options.PdfPipelineOptions()  # pyright: ignore
    pipeline_options.do_ocr = ocr == "on"
    format_options = {
        docling.datamodel.base_models.InputFormat.PDF: docling.document_converter.PdfFormatOption(  # pyright: ignore
            pipeline_options=pipeline_options
        ),
        docling.datamodel.base_models.InputFormat.IMAGE: docling.document_converter.ImageFormatOption(  # pyright: ignore
            pipeline_options=pipeline_options
        ),
    }
    return docling.document_converter.DocumentConverter(format_options=format_options)  # pyright: ignore
