import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
import tarfile
from datetime import date, datetime, time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Optional, Union
from urllib.parse import urlparse

import httpx
import lazy_loader as Lazy
from cyclopts import App

from tablassist.utils import (
    TIMEOUT,
    build_semantic_converter,
    get_biolink_html_documentation,
    get_html_as_markdown,
    get_json_response,
    get_static_content,
    get_xml_response,
    ledger_add,
    ledger_check,
    ledger_claim,
    ledger_release,
    load_ledger,
    parse_pmc_article_xml,
    parse_pmc_paper_summary,
    parse_yaml_string,
    pmc_paper_url,
    validate_config_root,
    validate_section,
    with_ncbi_api_key,
)

if TYPE_CHECKING:
    import fastexcel
    import polars as pl
    import textract
    import yaml
    from tablassert.enums import Categories, Predicates, Qualifiers
    from tablassert.ingests import from_yaml, to_sections
    from tablassert.models import Section
else:
    fastexcel = Lazy.load("fastexcel")
    pl = Lazy.load("polars")
    tablassert_enums = Lazy.load("tablassert.enums", suppress_warning=True)
    tablassert_ingests = Lazy.load("tablassert.ingests", suppress_warning=True)
    tablassert_models = Lazy.load("tablassert.models", suppress_warning=True)
    textract = Lazy.load("textract")
    yaml = Lazy.load("yaml")

CLI: App = App()


def json_safe(value: Any) -> Any:
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    return value


def column_summary(series: pl.Series) -> dict[str, Any]:
    dtype = series.dtype
    non_null = series.drop_nulls()

    summary: dict[str, Any] = {
        "name": series.name,
        "dtype": str(dtype),
        "null_count": series.null_count(),
        "non_null_count": non_null.len(),
        "unique_count": series.n_unique(),
        "sample_values": json_safe(non_null.unique(maintain_order=True).head(5).to_list()),
    }

    if non_null.is_empty():
        return summary

    if dtype.is_numeric():
        summary["statistics"] = json_safe(
            {
                "min": non_null.min(),
                "max": non_null.max(),
                "mean": non_null.mean(),
                "median": non_null.median(),
                "std": non_null.std(),
            }
        )
        return summary

    if dtype == pl.String:
        lengths = non_null.str.len_chars()
        summary["statistics"] = {
            "min_length": lengths.min(),
            "max_length": lengths.max(),
            "mean_length": lengths.mean(),
        }
        return summary

    if dtype == pl.Boolean:
        true_count = non_null.cast(pl.UInt8).sum()
        false_count = non_null.len() - true_count
        summary["statistics"] = {"true_count": true_count, "false_count": false_count}
        return summary

    if dtype.is_temporal():
        summary["statistics"] = json_safe({"min": non_null.min(), "max": non_null.max()})

    return summary


def explore_dataframe(df: pl.DataFrame) -> dict[str, Any]:
    return {
        "shape": {"rows": df.height, "columns": df.width},
        "schema": {name: str(dtype) for name, dtype in df.schema.items()},
        "sample_rows": json_safe(df.head(5).to_dicts()),
        "columns": [column_summary(df.get_column(name)) for name in df.columns],
    }


@CLI.command
def docs_table_config() -> str:
    """Fetch Tablassert table configuration spec documentation."""
    url: str = "https://raw.githubusercontent.com/SkyeAv/Tablassert/main/docs/configuration/table.md"
    return get_static_content(url)


TABLASSIST_USERNAME: str = os.environ.get("TABLASSIST_USERNAME", "")
TABLASSIST_API_KEY: str = os.environ.get("TABLASSIST_API_KEY", "")


def artifact_dirs(dest_dir: Path) -> dict[str, Path]:
    artifact_root = dest_dir
    raw_dir = artifact_root / "raw"
    source_dir = artifact_root / "source"
    derived_dir = artifact_root / "derived"
    scratch_dir = artifact_root / "scratch"
    for path in [artifact_root, raw_dir, source_dir, derived_dir, scratch_dir]:
        path.mkdir(parents=True, exist_ok=True)
    return {
        "artifact_root": artifact_root,
        "raw_dir": raw_dir,
        "source_dir": source_dir,
        "derived_dir": derived_dir,
        "scratch_dir": scratch_dir,
    }


def filename_from_headers(url: str, headers: httpx.Headers, fallback: str) -> str:
    disposition: str = headers.get("content-disposition", "")
    matches = re.search(r'filename="?([^";]+)"?', disposition)
    if matches:
        return Path(matches.group(1)).name

    parsed = urlparse(url)
    if parsed.path:
        candidate = Path(parsed.path).name
        if candidate:
            return candidate

    extension = mimetypes.guess_extension(headers.get("content-type", "").split(";", 1)[0].strip()) or ""
    if extension and not fallback.endswith(extension):
        return f"{fallback}{extension}"
    return fallback


def safe_extract_tar(archive_path: Path, dest_dir: Path) -> None:
    dest_root = dest_dir.resolve()
    with tarfile.open(archive_path) as archive:
        for member in archive.getmembers():
            target = (dest_dir / member.name).resolve()
            if os.path.commonpath([str(dest_root), str(target)]) != str(dest_root):
                raise ValueError(f"Refusing to extract archive member outside destination: {member.name}")
        archive.extractall(dest_dir)


@CLI.command
def search_curies(term: str) -> Union[list[Any], dict[str, Any]]:
    """Search CURIE candidates by term via Configurator API."""
    url: str = "https://hypatia.systemsbiology.net/configurator-api/search-for-curies"
    params: dict[str, Any] = {"username": TABLASSIST_USERNAME, "api-key": TABLASSIST_API_KEY, "term": term}

    return get_json_response(url, params)


@CLI.command
def download_pmc_tar(pmc_id: int, dest_dir: Path = Path(".")) -> dict[str, Any]:
    """Download and extract a PMC tar archive by PMC ID."""
    url: str = "https://hypatia.systemsbiology.net/configurator-api/download-from-pmc-tars"
    paths = artifact_dirs(dest_dir)

    params: dict[str, Any] = {"username": TABLASSIST_USERNAME, "api-key": TABLASSIST_API_KEY, "pmc-id": pmc_id}

    with httpx.stream("GET", url, params=params, timeout=TIMEOUT) as r:
        if r.status_code in [404, 400]:
            r.read()
            error: dict[str, Any] = r.json()
            return error

        filename = filename_from_headers(url, r.headers, "download.tar.xz")
        p: Path = paths["raw_dir"] / Path(filename).name
        with p.open("wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)

    safe_extract_tar(p, paths["source_dir"])

    files: list[str] = sorted(
        str(path.relative_to(paths["source_dir"])) for path in paths["source_dir"].rglob("*") if path.is_file()
    )
    archived = str(p)
    p.unlink()

    return {
        "status": "ok",
        "pmcid": pmc_id,
        "artifact_root": str(paths["artifact_root"]),
        "archive_path": archived,
        "source_dir": str(paths["source_dir"]),
        "files": files,
        "source_url": url,
        "paper_url": pmc_paper_url(pmc_id),
        "cleanup": {"removed": [archived]},
    }


@CLI.command
def download_url(url: str, dest_dir: Path = Path("."), filename: Optional[str] = None) -> dict[str, Any]:
    """Download a URL into a deterministic artifact directory."""
    paths = artifact_dirs(dest_dir)
    with httpx.stream("GET", url, follow_redirects=True, timeout=TIMEOUT) as response:
        response.raise_for_status()
        resolved_name = filename or filename_from_headers(url, response.headers, "download")
        target = paths["raw_dir"] / resolved_name
        with target.open("wb") as f:
            for chunk in response.iter_bytes():
                f.write(chunk)

    return {
        "status": "ok",
        "url": url,
        "artifact_root": str(paths["artifact_root"]),
        "path": str(target),
        "content_type": response.headers.get("content-type", ""),
    }


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
    return [x.value for x in tablassert_enums.Categories]  # pyright: ignore


@CLI.command
def list_predicates() -> list[str]:
    """List all supported Biolink predicates."""
    return [x.value for x in tablassert_enums.Predicates]  # pyright: ignore


@CLI.command
def list_qualifiers() -> list[str]:
    """List all supported Biolink qualifiers."""
    return [x.value for x in tablassert_enums.Qualifiers]  # pyright: ignore


@CLI.command
def section_schema() -> dict[str, Any]:
    """Return the Section Pydantic model as JSON schema."""
    return tablassert_models.Section.model_json_schema()  # pyright: ignore


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
    sections: list[Any] = tablassert_ingests.to_sections(raw, p)  # pyright: ignore

    errors: list[dict[str, Any]] = []
    for s in sections:
        errors += [validate_section(s)]

    return errors


@CLI.command
def validate_config_file(yaml_file: Path) -> Union[dict[str, Any], list[dict[str, Any]]]:
    """Validate a full YAML config file with top-level template and optional sections keys."""
    try:
        raw: Any = tablassert_ingests.from_yaml(yaml_file)  # pyright: ignore
    except yaml.scanner.ScannerError as e:  # pyright: ignore
        return {"error": f"YAML Syntax error at line {e.problem_mark.line + 1}: {e.problem}"}
    except yaml.parser.ParserError as e:  # pyright: ignore
        return {"error": f"YAML Parser error: {e}"}
    except yaml.YAMLError as e:
        return {"error": f"YAML error: {e}"}

    root_error: Optional[dict[str, Any]] = validate_config_root(raw)
    if root_error:
        return root_error

    sections: list[Any] = tablassert_ingests.to_sections(raw, yaml_file)  # pyright: ignore

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
def describe_excel(
    file: Path, sheet_name: str, engine: Literal["calamine", "openpyxl", "xlsx2csv"] = "calamine"
) -> dict[str, Any]:
    """Inspect an Excel sheet with schema, sample rows, and per-column profiles."""
    df: pl.DataFrame = pl.read_excel(source=file, sheet_name=sheet_name, engine=engine, infer_schema_length=None)
    summary = explore_dataframe(df)
    summary["sheet_name"] = sheet_name
    return summary


@CLI.command
def describe_csv(file: Path, separator: str = ",") -> dict[str, Any]:
    """Inspect a CSV/tabular file with schema, sample rows, and per-column profiles."""
    df: pl.DataFrame = pl.read_csv(source=file, separator=separator, infer_schema_length=None)
    summary = explore_dataframe(df)
    summary["separator"] = separator
    return summary


PMC_OA_BUCKET: str = "pmc-oa-opendata"
PMC_OA_LIST_TIMEOUT: float = 60.0
PMC_OA_COPY_TIMEOUT: float = 600.0


@CLI.command
def download_pmc_oa(pmc_id: int, dest_dir: Path = Path("."), version: Optional[int] = None) -> dict[str, Any]:
    """Download all files for a PMC article from the PMC OA S3 bucket via the AWS CLI.

    Lists available article-version prefixes under s3://pmc-oa-opendata/PMC<id>., picks the
    requested version (or the latest), and recursively downloads every object — XML, plain
    text, PDF, JSON metadata, media, and supplementary files — into <dest_dir>/PMC<id>.<ver>/.
    Uses --no-sign-request so no AWS account is required. Requires the `aws` CLI in PATH.
    """
    prefix: str = f"PMC{pmc_id}."

    list_cmd: list[str] = [
        "aws",
        "s3api",
        "list-objects-v2",
        "--bucket",
        PMC_OA_BUCKET,
        "--prefix",
        prefix,
        "--delimiter",
        "/",
        "--query",
        "CommonPrefixes[].Prefix",
        "--output",
        "text",
        "--no-sign-request",
    ]

    try:
        listing: subprocess.CompletedProcess[str] = subprocess.run(
            list_cmd, capture_output=True, text=True, timeout=PMC_OA_LIST_TIMEOUT
        )
    except FileNotFoundError:
        return {"error": "aws CLI not found in PATH"}
    except subprocess.TimeoutExpired:
        return {"error": f"aws s3api list-objects-v2 timed out after {PMC_OA_LIST_TIMEOUT}s"}

    if listing.returncode != 0:
        detail: str = listing.stderr.strip() or listing.stdout.strip() or "no output"
        return {"error": f"aws s3api list-objects-v2 failed: {detail}"}

    versions: list[tuple[int, str]] = []
    for raw in listing.stdout.split():
        candidate: str = raw.strip().rstrip("/")
        if "." not in candidate:
            continue
        _, ver_part = candidate.rsplit(".", 1)
        try:
            versions.append((int(ver_part), candidate))
        except ValueError:
            continue

    if not versions:
        return {"error": f"No PMC OA versions found for PMC{pmc_id}"}

    available: list[int] = sorted(v for v, _ in versions)
    if version is not None:
        chosen: Optional[tuple[int, str]] = next(((v, p) for v, p in versions if v == version), None)
        if chosen is None:
            return {"error": f"Version {version} not found for PMC{pmc_id}; available: {available}"}
    else:
        chosen = max(versions, key=lambda x: x[0])

    chosen_version: int = chosen[0]
    chosen_prefix: str = chosen[1]

    paths = artifact_dirs(dest_dir)
    target_dir: Path = paths["source_dir"] / chosen_prefix
    target_dir.mkdir(parents=True, exist_ok=True)

    cp_cmd: list[str] = [
        "aws",
        "s3",
        "cp",
        "--recursive",
        "--no-sign-request",
        f"s3://{PMC_OA_BUCKET}/{chosen_prefix}/",
        str(target_dir),
    ]

    try:
        cp: subprocess.CompletedProcess[str] = subprocess.run(
            cp_cmd, capture_output=True, text=True, timeout=PMC_OA_COPY_TIMEOUT
        )
    except FileNotFoundError:
        return {"error": "aws CLI not found in PATH"}
    except subprocess.TimeoutExpired:
        return {"error": f"aws s3 cp timed out after {PMC_OA_COPY_TIMEOUT}s"}

    if cp.returncode != 0:
        detail = cp.stderr.strip() or cp.stdout.strip() or "no output"
        return {"error": f"aws s3 cp failed: {detail}"}

    files: list[str] = sorted(str(p.relative_to(target_dir)) for p in target_dir.rglob("*") if p.is_file())

    return {
        "status": "ok",
        "pmcid": pmc_id,
        "version": chosen_version,
        "prefix": chosen_prefix,
        "artifact_root": str(paths["artifact_root"]),
        "dest_dir": str(target_dir),
        "source_dir": str(target_dir),
        "files": files,
        "available_versions": available,
        "s3_uri": f"s3://{PMC_OA_BUCKET}/{chosen_prefix}/",
        "s3_https_uri": f"https://{PMC_OA_BUCKET}.s3.amazonaws.com/{chosen_prefix}/",
        "paper_url": pmc_paper_url(pmc_id),
    }


PMC_ESEARCH_URL: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PMC_ESUMMARY_URL: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
PMC_EFETCH_URL: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


DATALAKE_DIRNAME: str = "DATALAKE"


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def datalake_target(launch_dir: Path, pmc_id: int, original: Path) -> tuple[Path, str]:
    target_name: str = f"PMC{int(pmc_id)}_{original.name}"
    return launch_dir / DATALAKE_DIRNAME / target_name, f"./{DATALAKE_DIRNAME}/{target_name}"


def iter_source_blocks(raw: Any) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    if not isinstance(raw, dict):
        return blocks
    template = raw.get("template")
    if isinstance(template, dict):
        src = template.get("source")
        if isinstance(src, dict):
            blocks.append(src)
    sections = raw.get("sections")
    if isinstance(sections, list):
        for sec in sections:
            if not isinstance(sec, dict):
                continue
            src = sec.get("source")
            if isinstance(src, dict):
                blocks.append(src)
    return blocks


def get_ncbi_result_error(payload: dict[str, Any]) -> Optional[str]:
    if error := payload.get("error") or payload.get("ERROR"):
        return str(error)

    error_list: Any = payload.get("errorlist")
    if isinstance(error_list, dict):
        details: list[str] = []
        for key, value in error_list.items():
            if isinstance(value, list) and value:
                details.append(f"{key}: {', '.join(str(item) for item in value)}")
        if details:
            return "; ".join(details)

    return None


@CLI.command
def search_pmc(query: str, max_results: int = 10, page: int = 0) -> dict[str, Any]:
    """Search PubMed Central for open-access articles with supplementary data."""
    full_query: str = f'"{query}" AND open access[filter]'
    esearch_params: dict[str, Any] = with_ncbi_api_key(
        {"db": "pmc", "retmode": "json", "retmax": max_results, "retstart": page * max_results, "term": full_query}
    )

    try:
        esearch: Any = get_json_response(PMC_ESEARCH_URL, esearch_params)
    except httpx.HTTPError as e:
        return {"error": f"PMC search failed: {e}"}

    if not isinstance(esearch, dict):
        return {"error": "PMC search returned a non-object response"}

    result: dict[str, Any] = esearch.get("esearchresult", {}) if isinstance(esearch.get("esearchresult"), dict) else {}
    if error := get_ncbi_result_error(result):
        return {"error": f"PMC search failed: {error}"}

    id_list: list[str] = result.get("idlist", []) or []
    count: int = int(result.get("count", 0) or 0)

    papers: list[dict[str, Any]] = []
    if id_list:
        esummary_params: dict[str, Any] = with_ncbi_api_key({"db": "pmc", "retmode": "json", "id": ",".join(id_list)})
        try:
            esummary: Any = get_json_response(PMC_ESUMMARY_URL, esummary_params)
        except httpx.HTTPError as e:
            return {"error": f"PMC summary lookup failed: {e}"}

        if not isinstance(esummary, dict):
            return {"error": "PMC summary lookup returned a non-object response"}

        summaries: dict[str, Any] = esummary.get("result", {}) if isinstance(esummary.get("result"), dict) else {}
        if error := get_ncbi_result_error(summaries):
            return {"error": f"PMC summary lookup failed: {error}"}

        for pmc_id in id_list:
            item: dict[str, Any] = summaries.get(pmc_id, {}) or {}
            papers.append(parse_pmc_paper_summary(pmc_id, item))

    return {"count": count, "papers": papers}


@CLI.command
def get_pmc_summary(pmc_id: int) -> dict[str, Any]:
    """Fetch detailed metadata and supplementary file list for a PMC article."""
    params: dict[str, Any] = with_ncbi_api_key({"db": "pmc", "id": pmc_id, "rettype": "xml"})
    try:
        root: Any = get_xml_response(PMC_EFETCH_URL, params)
    except Exception as e:
        return {"error": f"EFetch failed for PMC{pmc_id}: {e}"}

    return parse_pmc_article_xml(pmc_id, root)


@CLI.command
def consolidate_datalake(
    yaml_files: list[Path], pmc_id: int, artifact_root: Path, launch_dir: Path = Path(".")
) -> dict[str, Any]:
    """Move files referenced by `source.local` into a flat DATALAKE/ next to the configs.

    For each YAML, every unique `source.local` value is resolved relative to `artifact-root`
    (or used as-is if absolute), moved into `{launch-dir}/DATALAKE/PMC{pmc_id}_{basename}`,
    and the YAML's `source.local` is rewritten to `./DATALAKE/PMC{pmc_id}_{basename}`. Files
    already pointing inside `./DATALAKE/` are left in place (idempotent). Unreferenced files
    under `artifact-root` are not touched. The post-rewrite YAML is re-validated.
    """
    datalake_dir: Path = launch_dir / DATALAKE_DIRNAME
    moves: dict[str, dict[str, str]] = {}
    manifest: list[dict[str, str]] = []

    for yaml_file in yaml_files:
        if not yaml_file.is_file():
            return {"error": f"YAML file not found: {yaml_file}"}

        raw: Any = parse_yaml_string(yaml_file.read_text())
        if isinstance(raw, dict) and list(raw.keys()) == ["error"]:
            return {"error": f"Failed to parse {yaml_file}: {raw['error']}"}

        replacements: dict[str, str] = {}
        for src in iter_source_blocks(raw):
            local: Any = src.get("local")
            if not isinstance(local, str) or local in replacements:
                continue

            already_prefix: str = f"./{DATALAKE_DIRNAME}/"
            if local.startswith(already_prefix):
                rel: str = local[len(already_prefix) :]
                existing: Path = datalake_dir / rel
                if not existing.is_file():
                    return {"error": f"YAML {yaml_file} references {local} but the file is missing from DATALAKE"}
                replacements[local] = local
                manifest.append({"config_path": str(yaml_file), "original_path": str(existing), "datalake_path": local})
                continue

            cached: Optional[dict[str, str]] = moves.get(local)
            if cached is not None:
                replacements[local] = cached["datalake_path"]
                manifest.append(
                    {
                        "config_path": str(yaml_file),
                        "original_path": cached["original_path"],
                        "datalake_path": cached["datalake_path"],
                    }
                )
                continue

            original_resolved: Path = Path(local)
            if not original_resolved.is_absolute():
                original_resolved = artifact_root / original_resolved

            if not original_resolved.is_file():
                return {"error": f"Source file not found for {yaml_file}: {original_resolved}"}

            target, rewritten = datalake_target(launch_dir, pmc_id, original_resolved)
            datalake_dir.mkdir(parents=True, exist_ok=True)

            if target.exists():
                if target.resolve() == original_resolved.resolve():
                    pass
                elif hash_file(target) != hash_file(original_resolved):
                    return {
                        "error": (
                            f"DATALAKE collision: {target} already exists with different content than {original_resolved}"
                        )
                    }
                else:
                    original_resolved.unlink()
            else:
                shutil.move(str(original_resolved), str(target))

            replacements[local] = rewritten
            moves[local] = {"original_path": str(original_resolved), "datalake_path": rewritten}
            manifest.append(
                {"config_path": str(yaml_file), "original_path": str(original_resolved), "datalake_path": rewritten}
            )

        if replacements:
            for src in iter_source_blocks(raw):
                local = src.get("local")
                if isinstance(local, str) and local in replacements:
                    src["local"] = replacements[local]
            yaml_file.write_text(yaml.safe_dump(raw, sort_keys=False))  # pyright: ignore

    for yaml_file in yaml_files:
        validation: Any = validate_config_file(yaml_file)
        if isinstance(validation, dict) and "error" in validation:
            return {
                "error": f"Validation failed for {yaml_file} after consolidation: {validation['error']}",
                "manifest": manifest,
            }

    return {"status": "ok", "datalake_root": str(datalake_dir), "manifest": manifest}


@CLI.command
def discovery_ledger(
    action: Literal["read", "add", "check", "claim", "release"],
    ledger_path: Path,
    pmc_id: Optional[int] = None,
    status: Optional[str] = None,
    summary: Optional[str] = None,
    topic: Optional[str] = None,
    config_path: Optional[str] = None,
    config_paths: Optional[list[str]] = None,
    artifact_root: Optional[str] = None,
    agent_name: Optional[str] = None,
    run_id: Optional[str] = None,
    lease_seconds: int = 1800,
    paper_url: Optional[str] = None,
    s3_uri: Optional[str] = None,
    datalake_manifest: Optional[str] = None,
) -> dict[str, Any]:
    """Manage the discovery progress ledger (read/add/check entries)."""
    ledger = load_ledger(ledger_path, topic)
    if ledger is None or "error" in ledger:
        return ledger or {"error": "Failed to load ledger"}

    if action == "read":
        return ledger

    if action == "check":
        if pmc_id is None:
            return {"error": "check requires pmc_id"}
        return ledger_check(ledger, pmc_id)

    if action == "claim":
        if pmc_id is None:
            return {"error": "claim requires pmc_id"}
        return ledger_claim(ledger_path, topic, pmc_id, agent_name, run_id, lease_seconds)

    if action == "release":
        if pmc_id is None:
            return {"error": "release requires pmc_id"}
        return ledger_release(ledger_path, topic, pmc_id, run_id)

    if action == "add":
        if pmc_id is None or status is None:
            return {"error": "add requires pmc_id and status"}
        normalized_config_paths: list[str] = []
        if config_paths:
            normalized_config_paths = config_paths
        elif config_path:
            normalized_config_paths = [config_path]
        parsed_manifest: Optional[list[dict[str, str]]] = None
        if datalake_manifest is not None:
            try:
                raw_manifest: Any = json.loads(datalake_manifest)
            except json.JSONDecodeError as e:
                return {"error": f"datalake_manifest is not valid JSON: {e}"}
            if not isinstance(raw_manifest, list):
                return {"error": "datalake_manifest must be a JSON array"}
            parsed_manifest = []
            for item in raw_manifest:
                if not isinstance(item, dict):
                    return {"error": "datalake_manifest entries must be objects"}
                config_path_value = item.get("config_path")
                original_path_value = item.get("original_path")
                datalake_path_value = item.get("datalake_path")
                if not (
                    isinstance(config_path_value, str)
                    and isinstance(original_path_value, str)
                    and isinstance(datalake_path_value, str)
                ):
                    return {
                        "error": "datalake_manifest entries require string config_path, original_path, datalake_path"
                    }
                parsed_manifest.append(
                    {
                        "config_path": config_path_value,
                        "original_path": original_path_value,
                        "datalake_path": datalake_path_value,
                    }
                )
        return ledger_add(
            ledger_path,
            pmc_id,
            status,
            summary,
            topic,
            normalized_config_paths or None,
            artifact_root,
            agent_name,
            run_id,
            paper_url=paper_url,
            s3_uri=s3_uri,
            datalake_manifest=parsed_manifest,
        )


def serve() -> None:
    CLI()
