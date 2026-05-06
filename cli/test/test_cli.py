import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import tablassist.cli as cli
from tablassist.cli import (
    discovery_ledger,
    download_pmc_oa,
    extract_text_semantic,
    get_pmc_summary,
    list_categories,
    preview_csv,
    search_pmc,
    validate_config_file,
    validate_config_str,
    validate_section_str,
)


FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"


def test_list_categories_contains_gene() -> None:
    categories: list[str] = list_categories()
    assert "Gene" in categories


def test_preview_csv_reads_rows() -> None:
    preview: dict[str, list[str] | list[float]] = preview_csv(FIXTURES_DIR / "preview.csv", n_rows=1)

    assert preview == {"gene": ["BRCA1"], "score": [0.91]}


def test_validate_section_str_accepts_single_section() -> None:
    yaml_string = """
source:
  kind: text
  local: fixtures/preview.csv
  url: https://example.com/preview.csv
statement:
  subject:
    encoding: A
    method: column
  object:
    encoding: Gene
provenance:
  publication: PMC1234567
  contributors:
    - name: Example Curator
      date: \"2026-04-02\"
"""
    result = validate_section_str(yaml_string)

    assert result["status"] == "ok"


def test_validate_config_str_accepts_valid_fixture() -> None:
    result = validate_config_str((FIXTURES_DIR / "valid-config.yaml").read_text())

    assert isinstance(result, list)
    assert result[0]["status"] == "ok"


def test_validate_config_str_rejects_invalid_fixture() -> None:
    result = validate_config_str((FIXTURES_DIR / "invalid-config.yaml").read_text())

    assert isinstance(result, list)
    assert "error" in result[0]


def test_validate_config_str_requires_template_or_sections() -> None:
    yaml_string = """
source:
  kind: text
  local: fixtures/preview.csv
  url: https://example.com/preview.csv
statement:
  subject:
    encoding: A
    method: column
  object:
    encoding: Gene
provenance:
  publication: PMC1234567
  contributors:
    - name: Example Curator
      date: \"2026-04-02\"
"""
    result = validate_config_str(yaml_string)

    assert isinstance(result, dict)
    assert result["error"].startswith("Full YAML configs must include `template:`")


def test_validate_config_file_accepts_valid_fixture() -> None:
    result = validate_config_file(FIXTURES_DIR / "valid-config.yaml")

    assert isinstance(result, list)
    assert result[0]["status"] == "ok"


def test_extract_text_semantic_exports_requested_format(monkeypatch: Any) -> None:
    expected_file = FIXTURES_DIR / "preview.csv"
    strict_text_calls: list[bool] = []

    class FakeDocument:
        def export_to_markdown(self, strict_text: bool = False) -> str:
            strict_text_calls.append(strict_text)
            return "plain text" if strict_text else "# structured"

    class FakeResult:
        document = FakeDocument()

    class FakeConverter:
        def convert(self, file: Path) -> FakeResult:
            assert file == expected_file
            return FakeResult()

    def fake_builder(ocr: str = "auto") -> FakeConverter:
        assert ocr == "on"
        return FakeConverter()

    monkeypatch.setattr(cli, "build_semantic_converter", fake_builder)

    assert extract_text_semantic(expected_file, output_format="text", ocr="on") == "plain text"
    assert strict_text_calls == [True]


def test_extract_text_semantic_returns_import_error(monkeypatch: Any) -> None:
    def fake_builder(ocr: str = "auto") -> Any:
        raise ImportError("missing docling")

    monkeypatch.setattr(cli, "build_semantic_converter", fake_builder)

    assert extract_text_semantic(FIXTURES_DIR / "preview.csv") == "ERROR | missing docling"


def test_search_pmc_returns_structured_results(monkeypatch: Any) -> None:
    captured: list[tuple[str, dict[str, Any]]] = []

    def fake_json_response(url: str, params: dict[str, Any]) -> dict[str, Any]:
        captured.append((url, params))
        if url.endswith("esearch.fcgi"):
            return {"esearchresult": {"count": "2", "idlist": ["111", "222"]}}
        return {
            "result": {
                "111": {
                    "title": "Paper One",
                    "pubdate": "2024",
                    "authors": [{"name": "Jane Doe"}, {"name": "John Roe"}],
                    "articleids": [{"name": "pmcid"}],
                },
                "222": {
                    "title": "Paper Two",
                    "pubdate": "2025",
                    "authors": [{"name": "Ada Lovelace"}],
                    "articleids": [],
                },
            }
        }

    monkeypatch.setattr(cli, "get_json_response", fake_json_response)

    result = search_pmc("cancer", max_results=2, page=0)
    assert result["count"] == 2
    assert [p["pmcid"] for p in result["papers"]] == [111, 222]
    assert result["papers"][0]["title"] == "Paper One"
    assert result["papers"][0]["authors"] == ["Jane Doe", "John Roe"]
    assert captured[0][0].endswith("esearch.fcgi")
    assert "open access" in captured[0][1]["term"]
    assert "supplementary materials" not in captured[0][1]["term"]


def test_search_pmc_handles_no_results(monkeypatch: Any) -> None:
    def fake_json_response(url: str, params: dict[str, Any]) -> dict[str, Any]:
        return {"esearchresult": {"count": "0", "idlist": []}}

    monkeypatch.setattr(cli, "get_json_response", fake_json_response)

    assert search_pmc("nothing") == {"count": 0, "papers": []}


def test_search_pmc_handles_ncbi_error_payload(monkeypatch: Any) -> None:
    def fake_json_response(url: str, params: dict[str, Any]) -> dict[str, Any]:
        return {"esearchresult": {"ERROR": "API key invalid"}}

    monkeypatch.setattr(cli, "get_json_response", fake_json_response)

    assert search_pmc("nothing") == {"error": "PMC search failed: API key invalid"}


def test_search_pmc_handles_ncbi_error_list(monkeypatch: Any) -> None:
    def fake_json_response(url: str, params: dict[str, Any]) -> dict[str, Any]:
        return {"esearchresult": {"errorlist": {"phrasesnotfound": ["materials"]}}}

    monkeypatch.setattr(cli, "get_json_response", fake_json_response)

    assert search_pmc("nothing") == {"error": "PMC search failed: phrasesnotfound: materials"}


def test_search_pmc_handles_summary_error_payload(monkeypatch: Any) -> None:
    def fake_json_response(url: str, params: dict[str, Any]) -> dict[str, Any]:
        if url.endswith("esearch.fcgi"):
            return {"esearchresult": {"count": "1", "idlist": ["111"]}}
        return {"result": {"error": "rate limit"}}

    monkeypatch.setattr(cli, "get_json_response", fake_json_response)

    assert search_pmc("nothing") == {"error": "PMC summary lookup failed: rate limit"}


def test_get_pmc_summary_parses_xml(monkeypatch: Any) -> None:
    sample_xml = """<?xml version="1.0"?>
<root>
  <article>
    <front>
      <article-meta>
        <title-group><article-title>A Great Paper</article-title></title-group>
        <contrib-group>
          <contrib contrib-type="author">
            <name><surname>Doe</surname><given-names>Jane</given-names></name>
          </contrib>
        </contrib-group>
        <abstract><p>Abstract text.</p></abstract>
      </article-meta>
    </front>
    <body>
      <sec>
        <supplementary-material id="s1">
          <media xlink:href="supp1.xlsx" mimetype="application/vnd.ms-excel"
                 xmlns:xlink="http://www.w3.org/1999/xlink"/>
        </supplementary-material>
      </sec>
    </body>
  </article>
</root>
"""

    def fake_xml(url: str, params: dict[str, Any]) -> ET.Element:
        return ET.fromstring(sample_xml)

    monkeypatch.setattr(cli, "get_xml_response", fake_xml)

    result = get_pmc_summary(12345)
    assert result["pmcid"] == 12345
    assert result["title"] == "A Great Paper"
    assert "Abstract text." in result["abstract"]
    assert result["authors"] == ["Jane Doe"]
    assert result["supplements"] == [{"filename": "supp1.xlsx", "media_type": "application/vnd.ms-excel"}]


def test_discovery_ledger_round_trip(tmp_path: Path) -> None:
    ledger_path = tmp_path / "ledger.json"

    assert discovery_ledger("read", ledger_path) == {"topic": "", "entries": []}

    added = discovery_ledger(
        "add",
        ledger_path,
        pmc_id=42,
        status="success",
        summary="worked",
        topic="cancer",
        config_paths=["ROMERO3.yaml", "ROMERO3B.yaml"],
    )
    assert added["added"]["pmcid"] == 42
    assert added["added"]["config_paths"] == ["ROMERO3.yaml", "ROMERO3B.yaml"]
    assert added["total_entries"] == 1

    check_hit = discovery_ledger("check", ledger_path, pmc_id=42)
    assert check_hit["exists"] is True
    assert check_hit["entry"]["status"] == "success"

    assert discovery_ledger("check", ledger_path, pmc_id=99) == {"exists": False, "entry": None}

    disk = json.loads(ledger_path.read_text())
    assert disk["topic"] == "cancer"
    assert disk["entries"][0]["pmcid"] == 42
    assert disk["entries"][0]["config_paths"] == ["ROMERO3.yaml", "ROMERO3B.yaml"]


def test_discovery_ledger_read_normalizes_legacy_config_path(tmp_path: Path) -> None:
    ledger_path = tmp_path / "ledger.json"
    ledger_path.write_text(
        json.dumps({"topic": "cancer", "entries": [{"pmcid": 42, "status": "success", "config_path": "ROMERO3.yaml"}]})
    )

    result = discovery_ledger("read", ledger_path)

    assert result["entries"][0]["config_paths"] == ["ROMERO3.yaml"]


def test_discovery_ledger_add_requires_fields(tmp_path: Path) -> None:
    ledger_path = tmp_path / "ledger.json"
    result = discovery_ledger("add", ledger_path, pmc_id=None, status="success")
    assert "error" in result


def stub_subprocess_run(monkeypatch: Any, handlers: list[Any], captured: list[list[str]] | None = None) -> None:
    """Replace subprocess.run with a queue of handlers; each handler is a callable taking the cmd list."""
    queue = list(handlers)

    def fake_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if captured is not None:
            captured.append(list(cmd))
        if not queue:
            raise AssertionError(f"unexpected subprocess.run call: {cmd}")
        handler = queue.pop(0)
        return handler(cmd)

    monkeypatch.setattr(cli.subprocess, "run", fake_run)


def test_download_pmc_oa_picks_latest_version(monkeypatch: Any, tmp_path: Path) -> None:
    captured: list[list[str]] = []

    def list_handler(cmd: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="PMC11370360.1/\nPMC11370360.2/\n", stderr="")

    def cp_handler(cmd: list[str]) -> subprocess.CompletedProcess[str]:
        target = Path(cmd[-1])
        target.mkdir(parents=True, exist_ok=True)
        (target / "PMC11370360.2.xml").write_text("<xml/>")
        (target / "PMC11370360.2.txt").write_text("hello")
        (target / "PMC11370360.2.json").write_text("{}")
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="download: ok\n", stderr="")

    stub_subprocess_run(monkeypatch, [list_handler, cp_handler], captured)

    result = download_pmc_oa(11370360, dest_dir=tmp_path)

    assert result["status"] == "ok"
    assert result["pmcid"] == 11370360
    assert result["version"] == 2
    assert result["prefix"] == "PMC11370360.2"
    assert result["available_versions"] == [1, 2]
    assert result["dest_dir"] == str(tmp_path / "PMC11370360.2")
    assert result["files"] == ["PMC11370360.2.json", "PMC11370360.2.txt", "PMC11370360.2.xml"]

    list_cmd, cp_cmd = captured
    assert list_cmd[:2] == ["aws", "s3api"]
    assert "--no-sign-request" in list_cmd
    assert "PMC11370360." in list_cmd
    assert cp_cmd[:3] == ["aws", "s3", "cp"]
    assert "--recursive" in cp_cmd
    assert "--no-sign-request" in cp_cmd
    assert cp_cmd[-2] == "s3://pmc-oa-opendata/PMC11370360.2/"


def test_download_pmc_oa_honors_explicit_version(monkeypatch: Any, tmp_path: Path) -> None:
    captured: list[list[str]] = []

    def list_handler(cmd: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout="PMC9999.1/\tPMC9999.2/\tPMC9999.3/\n", stderr=""
        )

    def cp_handler(cmd: list[str]) -> subprocess.CompletedProcess[str]:
        target = Path(cmd[-1])
        target.mkdir(parents=True, exist_ok=True)
        (target / "PMC9999.1.xml").write_text("<xml/>")
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    stub_subprocess_run(monkeypatch, [list_handler, cp_handler], captured)

    result = download_pmc_oa(9999, dest_dir=tmp_path, version=1)

    assert result["status"] == "ok"
    assert result["version"] == 1
    assert captured[1][-2] == "s3://pmc-oa-opendata/PMC9999.1/"


def test_download_pmc_oa_unknown_version_returns_error(monkeypatch: Any, tmp_path: Path) -> None:
    def list_handler(cmd: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="PMC42.1/\n", stderr="")

    stub_subprocess_run(monkeypatch, [list_handler])

    result = download_pmc_oa(42, dest_dir=tmp_path, version=7)

    assert "error" in result
    assert "Version 7 not found" in result["error"]
    assert "[1]" in result["error"]


def test_download_pmc_oa_no_versions_found(monkeypatch: Any, tmp_path: Path) -> None:
    def list_handler(cmd: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="\n", stderr="")

    stub_subprocess_run(monkeypatch, [list_handler])

    result = download_pmc_oa(123, dest_dir=tmp_path)

    assert result == {"error": "No PMC OA versions found for PMC123"}


def test_download_pmc_oa_list_failure_surfaces_stderr(monkeypatch: Any, tmp_path: Path) -> None:
    def list_handler(cmd: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="AccessDenied")

    stub_subprocess_run(monkeypatch, [list_handler])

    result = download_pmc_oa(123, dest_dir=tmp_path)

    assert "error" in result
    assert "AccessDenied" in result["error"]


def test_download_pmc_oa_cp_failure_surfaces_stderr(monkeypatch: Any, tmp_path: Path) -> None:
    def list_handler(cmd: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="PMC42.1/\n", stderr="")

    def cp_handler(cmd: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="fatal error")

    stub_subprocess_run(monkeypatch, [list_handler, cp_handler])

    result = download_pmc_oa(42, dest_dir=tmp_path)

    assert "error" in result
    assert "aws s3 cp failed" in result["error"]
    assert "fatal error" in result["error"]


def test_download_pmc_oa_missing_aws_cli(monkeypatch: Any, tmp_path: Path) -> None:
    def list_handler(cmd: list[str]) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError("aws not found")

    stub_subprocess_run(monkeypatch, [list_handler])

    result = download_pmc_oa(42, dest_dir=tmp_path)

    assert result == {"error": "aws CLI not found in PATH"}
