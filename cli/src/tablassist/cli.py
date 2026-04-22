import datetime as dt
import json
import os
import re
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Optional, Union

import fastexcel
import httpx
import lazy_loader as Lazy
import polars as pl
import yaml
from cyclopts import App
from tablassert.enums import Categories, Predicates, Qualifiers
from tablassert.ingests import from_yaml, to_sections
from tablassert.models import Section

from tablassist.utils import (
    TIMEOUT,
    build_semantic_converter,
    get_biolink_html_documentation,
    get_html_as_markdown,
    get_json_response,
    get_static_content,
    get_xml_response,
    parse_pmc_supplements,
    parse_yaml_string,
    validate_config_root,
    validate_section,
    with_ncbi_api_key,
)

if TYPE_CHECKING:
    import textract
else:
    textract = Lazy.load("textract")

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

    with httpx.stream("GET", url, params=params, timeout=TIMEOUT) as r:
        if r.status_code in [404, 400]:
            r.read()
            error: dict[str, Any] = r.json()
            return error

        d: str = r.headers.get("content-disposition", "")
        matches: object = re.search(r"filename=(.+)", d)

        filename: str = matches.group(1) if matches else "download.tar.xz"
        p: Path = dest_dir / filename
        with p.open("wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)

    cmd: str = f"tar -xvf '{p}' && rm '{p}' && ls -lh '{dest_dir}'"
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
    """Validate a single YAML section dict from a string, without template/sections merging."""
    raw: Any = parse_yaml_string(yaml_string)
    if isinstance(raw, dict) and "error" in raw:
        return raw

    return validate_section(raw)


@CLI.command
def validate_config_str(yaml_string: str) -> Union[dict[str, Any], list[dict[str, Any]]]:
    """Validate a full YAML config string with top-level template and optional sections keys."""
    raw: Any = parse_yaml_string(yaml_string)
    if isinstance(raw, dict) and "error" in raw:
        return raw

    root_error: Optional[dict[str, Any]] = validate_config_root(raw)
    if root_error:
        return root_error

    p: Path = Path(".")
    sections: list[Any] = to_sections(raw, p)

    errors: list[dict[str, Any]] = []
    for s in sections:
        errors += [validate_section(s)]

    return errors


@CLI.command
def validate_config_file(yaml_file: Path) -> Union[dict[str, Any], list[dict[str, Any]]]:
    """Validate a full YAML config file with top-level template and optional sections keys."""
    try:
        raw: Any = from_yaml(yaml_file)
    except yaml.scanner.ScannerError as e:  # pyright: ignore
        return {"error": f"YAML Syntax error at line {e.problem_mark.line + 1}: {e.problem}"}
    except yaml.parser.ParserError as e:  # pyright: ignore
        return {"error": f"YAML Parser error: {e}"}
    except yaml.YAMLError as e:
        return {"error": f"YAML error: {e}"}

    root_error: Optional[dict[str, Any]] = validate_config_root(raw)
    if root_error:
        return root_error

    sections: list[Any] = to_sections(raw, yaml_file)

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
    if file.suffix.lower() == ".pdf":
        return textract.process(file, method="pdfminer")
    elif extension:
        return textract.process(file, extension=extension)
    else:
        return textract.process(file)


@CLI.command
def extract_text_semantic(
    file: Path, output_format: Literal["markdown", "text"] = "markdown", ocr: Literal["auto", "off", "on"] = "auto"
) -> str:
    """Extract semantic text with Docling as Markdown or plain text."""
    try:
        result: Any = build_semantic_converter(ocr).convert(file)
    except ImportError as e:
        return f"ERROR | {e}"
    except Exception as e:
        return f"ERROR | {e}"

    if output_format == "text":
        return result.document.export_to_markdown(strict_text=True)

    return result.document.export_to_markdown()


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


@CLI.command
def pmc_oa_readme() -> str:
    """Fetch the PMC Open Access dataset README with download instructions and file format details."""
    url: str = "https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/"
    return get_html_as_markdown(url)


PMC_ESEARCH_URL: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PMC_ESUMMARY_URL: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
PMC_EFETCH_URL: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


@CLI.command
def search_pmc(query: str, max_results: int = 10, page: int = 0) -> dict[str, Any]:
    """Search PubMed Central for open-access articles with supplementary data."""
    full_query: str = f'"{query}" AND open access[filter] AND supplementary materials[filter]'
    esearch_params: dict[str, Any] = with_ncbi_api_key(
        {"db": "pmc", "retmode": "json", "retmax": max_results, "retstart": page * max_results, "term": full_query}
    )

    esearch: Any = get_json_response(PMC_ESEARCH_URL, esearch_params)
    result: dict[str, Any] = esearch.get("esearchresult", {}) if isinstance(esearch, dict) else {}
    id_list: list[str] = result.get("idlist", []) or []
    count: int = int(result.get("count", 0) or 0)

    papers: list[dict[str, Any]] = []
    if id_list:
        esummary_params: dict[str, Any] = with_ncbi_api_key({"db": "pmc", "retmode": "json", "id": ",".join(id_list)})
        esummary: Any = get_json_response(PMC_ESUMMARY_URL, esummary_params)
        summaries: dict[str, Any] = esummary.get("result", {}) if isinstance(esummary, dict) else {}
        for pmc_id in id_list:
            item: dict[str, Any] = summaries.get(pmc_id, {}) or {}
            authors_field: list[dict[str, Any]] = item.get("authors", []) or []
            authors: list[str] = [a.get("name", "") for a in authors_field if a.get("name")]
            has_suppl: bool = any(
                "suppl" in (a.get("name", "") or "").lower() for a in item.get("articleids", []) or []
            )
            papers.append(
                {
                    "pmcid": int(pmc_id),
                    "title": item.get("title", ""),
                    "authors": authors,
                    "date": item.get("pubdate", ""),
                    "has_suppl_data": has_suppl,
                }
            )

    return {"count": count, "papers": papers}


@CLI.command
def get_pmc_summary(pmc_id: int) -> dict[str, Any]:
    """Fetch detailed metadata and supplementary file list for a PMC article."""
    params: dict[str, Any] = with_ncbi_api_key({"db": "pmc", "id": pmc_id, "rettype": "xml"})
    try:
        root: Any = get_xml_response(PMC_EFETCH_URL, params)
    except Exception as e:
        return {"error": f"EFetch failed for PMC{pmc_id}: {e}"}

    title_el: Any = next(iter(root.iter("article-title")), None)
    title: str = "".join(title_el.itertext()).strip() if title_el is not None else ""

    abstract_el: Any = next(iter(root.iter("abstract")), None)
    abstract: str = "".join(abstract_el.itertext()).strip() if abstract_el is not None else ""

    authors: list[str] = []
    for contrib in root.iter("contrib"):
        if contrib.get("contrib-type") and contrib.get("contrib-type") != "author":
            continue
        surname_el: Any = next(iter(contrib.iter("surname")), None)
        given_el: Any = next(iter(contrib.iter("given-names")), None)
        surname: str = surname_el.text.strip() if surname_el is not None and surname_el.text else ""
        given: str = given_el.text.strip() if given_el is not None and given_el.text else ""
        name: str = f"{given} {surname}".strip()
        if name:
            authors.append(name)

    supplements: list[dict[str, str]] = parse_pmc_supplements(root)

    return {"pmcid": pmc_id, "title": title, "abstract": abstract, "authors": authors, "supplements": supplements}


@CLI.command
def discovery_ledger(
    action: Literal["read", "add", "check"],
    ledger_path: Path,
    pmc_id: Optional[int] = None,
    status: Optional[str] = None,
    summary: Optional[str] = None,
    topic: Optional[str] = None,
    config_path: Optional[str] = None,
) -> dict[str, Any]:
    """Manage the discovery progress ledger (read/add/check entries)."""
    ledger: dict[str, Any]
    if ledger_path.exists():
        try:
            ledger = json.loads(ledger_path.read_text())
        except json.JSONDecodeError as e:
            return {"error": f"Ledger JSON parse error: {e}"}
    else:
        ledger = {"topic": topic or "", "entries": []}

    if action == "read":
        return ledger

    if action == "check":
        if pmc_id is None:
            return {"error": "check requires pmc_id"}
        for entry in ledger.get("entries", []):
            if int(entry.get("pmcid", -1)) == int(pmc_id):
                return {"exists": True, "entry": entry}
        return {"exists": False, "entry": None}

    if action == "add":
        if pmc_id is None or status is None:
            return {"error": "add requires pmc_id and status"}
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
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(json.dumps(ledger, indent=2))
        return {"added": entry, "total_entries": len(ledger["entries"])}

    return {"error": f"unknown action: {action}"}


def serve() -> None:
    CLI()
