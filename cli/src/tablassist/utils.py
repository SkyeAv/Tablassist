import datetime as dt
import os
import json
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Optional, Union
from urllib.parse import quote

import httpx
import lazy_loader as Lazy

if TYPE_CHECKING:
    import docling
    import trafilatura
    import yaml
    from pydantic import ValidationError
    from tablassert.models import Section
else:
    docling = Lazy.load("docling")
    pydantic = Lazy.load("pydantic")
    tablassert_models = Lazy.load("tablassert.models", suppress_warning=True)
    trafilatura = Lazy.load("trafilatura")
    yaml = Lazy.load("yaml")

TIMEOUT: float = 60.0  # seconds

NCBI_API_KEY: str = os.environ.get("NCBI_API_KEY", "")

PMC_ESEARCH_URL: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PMC_ESUMMARY_URL: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
PMC_EFETCH_URL: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

XLINK_HREF: str = "{http://www.w3.org/1999/xlink}href"
LEDGER_VERSION: int = 2
CLAIM_LEASE_SECONDS_DEFAULT: int = 1800
LEDGER_LOCK_TIMEOUT_SECONDS: float = 10.0
LEDGER_LOCK_STALE_SECONDS: float = 60.0


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

    return {
        "pmcid": int(pmc_id),
        "title": item.get("title", ""),
        "authors": authors,
        "date": item.get("pubdate", ""),
        "has_suppl_data": False,
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


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _default_ledger(topic: Optional[str]) -> dict[str, Any]:
    now: str = _utc_now_iso()
    return {"version": LEDGER_VERSION, "topic": topic or "", "entries": [], "claims": {}, "updated_at": now}


def _normalize_ledger(ledger: dict[str, Any], topic: Optional[str]) -> dict[str, Any]:
    normalized: dict[str, Any] = _default_ledger(topic)
    normalized["topic"] = str(ledger.get("topic") or topic or "")

    raw_claims = ledger.get("claims")
    claims: dict[str, Any] = raw_claims if isinstance(raw_claims, dict) else {}
    active_claims: dict[str, Any] = {}
    now = _utc_now()
    for key, claim in claims.items():
        if not isinstance(claim, dict):
            continue
        expires_at = claim.get("expires_at")
        if isinstance(expires_at, str):
            try:
                if dt.datetime.fromisoformat(expires_at) <= now:
                    continue
            except ValueError:
                continue
        active_claims[str(key)] = claim

    entries_by_pmcid: dict[int, dict[str, Any]] = {}
    for raw_entry in ledger.get("entries", []):
        if not isinstance(raw_entry, dict):
            continue
        raw_pmcid = raw_entry.get("pmcid")
        if raw_pmcid is None:
            continue
        try:
            pmcid = int(raw_pmcid)
        except (TypeError, ValueError):
            continue

        timestamp = raw_entry.get("timestamp") if isinstance(raw_entry.get("timestamp"), str) else None
        created_at = (
            raw_entry.get("created_at") if isinstance(raw_entry.get("created_at"), str) else timestamp or _utc_now_iso()
        )
        updated_at = raw_entry.get("updated_at") if isinstance(raw_entry.get("updated_at"), str) else created_at
        config_paths = raw_entry.get("config_paths")
        if not isinstance(config_paths, list):
            legacy_config_path = raw_entry.get("config_path")
            config_paths = [legacy_config_path] if isinstance(legacy_config_path, str) else []

        entry: dict[str, Any] = {
            "pmcid": pmcid,
            "status": str(raw_entry.get("status") or "unknown"),
            "summary": str(raw_entry.get("summary") or ""),
            "config_paths": [str(path) for path in config_paths],
            "created_at": created_at,
            "updated_at": updated_at,
        }
        if isinstance(raw_entry.get("artifact_root"), str):
            entry["artifact_root"] = raw_entry["artifact_root"]
        if isinstance(raw_entry.get("completed_at"), str):
            entry["completed_at"] = raw_entry["completed_at"]
        elif entry["status"] not in {"claimed", "in-progress"}:
            entry["completed_at"] = updated_at

        claim = active_claims.get(str(pmcid))
        if claim:
            entry["claim"] = claim

        current = entries_by_pmcid.get(pmcid)
        if current is None or str(entry["updated_at"]) >= str(current.get("updated_at", "")):
            entries_by_pmcid[pmcid] = entry

    normalized["entries"] = sorted(entries_by_pmcid.values(), key=lambda item: int(item["pmcid"]))
    normalized["claims"] = active_claims
    normalized["updated_at"] = str(ledger.get("updated_at") or _utc_now_iso())
    return normalized


def load_ledger(ledger_path: Path, topic: Optional[str]) -> Union[dict[str, Any], None]:
    if not ledger_path.exists():
        return _default_ledger(topic)
    try:
        raw = json.loads(ledger_path.read_text())
    except json.JSONDecodeError as e:
        return {"error": f"Ledger JSON parse error: {e}"}
    if not isinstance(raw, dict):
        return {"error": "Ledger JSON must be an object"}
    return _normalize_ledger(raw, topic)


def _lock_path_for_ledger(ledger_path: Path) -> Path:
    return ledger_path.with_suffix(f"{ledger_path.suffix}.lock")


def _acquire_ledger_lock(ledger_path: Path) -> Path:
    lock_path = _lock_path_for_ledger(ledger_path)
    deadline = time.monotonic() + LEDGER_LOCK_TIMEOUT_SECONDS
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w") as lock_file:
                lock_file.write(str(os.getpid()))
            return lock_path
        except FileExistsError:
            try:
                age = time.time() - lock_path.stat().st_mtime
            except FileNotFoundError:
                continue
            if age > LEDGER_LOCK_STALE_SECONDS:
                try:
                    lock_path.unlink()
                except FileNotFoundError:
                    continue
                continue
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Timed out waiting for ledger lock: {lock_path}")
            time.sleep(0.05)


def _release_ledger_lock(lock_path: Path) -> None:
    try:
        lock_path.unlink()
    except FileNotFoundError:
        pass


def _write_ledger_unlocked(ledger_path: Path, ledger: dict[str, Any]) -> None:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", dir=ledger_path.parent, prefix=f".{ledger_path.name}.", suffix=".tmp", delete=False
    ) as f:
        json.dump(ledger, f, indent=2)
        f.write("\n")
        tmp_path = Path(f.name)
    os.replace(tmp_path, ledger_path)


def write_ledger(ledger_path: Path, ledger: dict[str, Any]) -> None:
    lock_path = _acquire_ledger_lock(ledger_path)
    try:
        _write_ledger_unlocked(ledger_path, _normalize_ledger(ledger, ledger.get("topic")))
    finally:
        _release_ledger_lock(lock_path)


def update_ledger(ledger_path: Path, topic: Optional[str], update_fn: Any) -> dict[str, Any]:
    lock_path = _acquire_ledger_lock(ledger_path)
    try:
        ledger = load_ledger(ledger_path, topic)
        if ledger is None or "error" in ledger:
            return ledger or {"error": "Failed to load ledger"}
        normalized = _normalize_ledger(ledger, topic)
        result: dict[str, Any] = update_fn(normalized)
        normalized["updated_at"] = _utc_now_iso()
        _write_ledger_unlocked(ledger_path, normalized)
        return result
    finally:
        _release_ledger_lock(lock_path)


def ledger_check(ledger: dict[str, Any], pmc_id: int) -> dict[str, Any]:
    for entry in ledger.get("entries", []):
        if int(entry.get("pmcid", -1)) == int(pmc_id):
            claim = ledger.get("claims", {}).get(str(pmc_id))
            return {"exists": True, "entry": entry, "claimed": claim is not None, "claim": claim}
    claim = ledger.get("claims", {}).get(str(pmc_id))
    return {"exists": False, "entry": None, "claimed": claim is not None, "claim": claim}


def ledger_claim(
    ledger_path: Path,
    topic: Optional[str],
    pmc_id: int,
    agent_name: Optional[str],
    run_id: Optional[str],
    lease_seconds: int,
) -> dict[str, Any]:
    def _claim(ledger: dict[str, Any]) -> dict[str, Any]:
        key = str(int(pmc_id))
        existing = ledger.get("claims", {}).get(key)
        if existing and existing.get("run_id") != run_id:
            return {"claimed": False, "claim": existing, "error": f"PMC{pmc_id} is already claimed"}

        claimed_at = _utc_now_iso()
        claim = {
            "pmcid": int(pmc_id),
            "agent_name": agent_name or "",
            "run_id": run_id or "",
            "claimed_at": claimed_at,
            "expires_at": (_utc_now() + dt.timedelta(seconds=lease_seconds)).isoformat(),
        }
        ledger.setdefault("claims", {})[key] = claim

        for entry in ledger.get("entries", []):
            if int(entry.get("pmcid", -1)) == int(pmc_id):
                entry["claim"] = claim
                entry["updated_at"] = claimed_at
                break

        return {"claimed": True, "claim": claim}

    return update_ledger(ledger_path, topic, _claim)


def ledger_release(ledger_path: Path, topic: Optional[str], pmc_id: int, run_id: Optional[str]) -> dict[str, Any]:
    def _release(ledger: dict[str, Any]) -> dict[str, Any]:
        key = str(int(pmc_id))
        existing = ledger.get("claims", {}).get(key)
        if existing is None:
            return {"released": False, "claim": None}
        if run_id and existing.get("run_id") and existing.get("run_id") != run_id:
            return {"released": False, "claim": existing, "error": f"PMC{pmc_id} is claimed by another run"}

        del ledger.setdefault("claims", {})[key]
        for entry in ledger.get("entries", []):
            if int(entry.get("pmcid", -1)) == int(pmc_id):
                entry.pop("claim", None)
                entry["updated_at"] = _utc_now_iso()
                break
        return {"released": True, "claim": existing}

    return update_ledger(ledger_path, topic, _release)


def ledger_add(
    ledger_path: Path,
    pmc_id: int,
    status: str,
    summary: Optional[str],
    topic: Optional[str],
    config_paths: Optional[list[str]],
    artifact_root: Optional[str],
    agent_name: Optional[str],
    run_id: Optional[str],
) -> dict[str, Any]:
    def _add(ledger: dict[str, Any]) -> dict[str, Any]:
        now = _utc_now_iso()
        if topic and not ledger.get("topic"):
            ledger["topic"] = topic

        entry = next((item for item in ledger.get("entries", []) if int(item.get("pmcid", -1)) == int(pmc_id)), None)
        if entry is None:
            entry = {"pmcid": int(pmc_id), "created_at": now}
            ledger.setdefault("entries", []).append(entry)

        entry["status"] = status
        entry["summary"] = summary or ""
        entry["config_paths"] = [str(path) for path in (config_paths or [])]
        entry["updated_at"] = now
        if artifact_root:
            entry["artifact_root"] = artifact_root
        if status not in {"claimed", "in-progress"}:
            entry["completed_at"] = now

        claim = ledger.get("claims", {}).get(str(int(pmc_id)))
        if claim is not None:
            if run_id and claim.get("run_id") and claim.get("run_id") != run_id:
                return {"error": f"PMC{pmc_id} is claimed by another run", "claim": claim}
            del ledger.setdefault("claims", {})[str(int(pmc_id))]
            entry.pop("claim", None)

        entry["updated_by"] = {"agent_name": agent_name or "", "run_id": run_id or ""}
        ledger["entries"] = sorted(ledger.get("entries", []), key=lambda item: int(item["pmcid"]))
        return {"added": entry, "total_entries": len(ledger["entries"])}

    return update_ledger(ledger_path, topic, _add)


def get_html_as_markdown(url: str) -> str:
    html: str = get_static_content(url)
    return trafilatura.extract(html, output_format="markdown") or ""


def get_biolink_html_documentation(biolink_thing: str) -> str:
    url: str = f"https://raw.githubusercontent.com/biolink/biolink-model/gh-pages/{quote(biolink_thing)}/index.html"
    return get_html_as_markdown(url)


def validate_section(s: dict[str, Any]) -> dict[str, Any]:
    section: dict[str, Any] = {k: v for k, v in s.items() if k != "config"}

    try:
        tablassert_models.Section.model_validate(section)  # pyright: ignore
        return {"section": section, "status": "ok"}
    except pydantic.ValidationError as e:  # pyright: ignore
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
        return yaml.load(yaml_string, Loader=yaml.CLoader)  # pyright: ignore
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
