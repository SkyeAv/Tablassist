import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from unittest.mock import patch

import polars as pl
import tablassist.cli as cli
import yaml
from tablassist.cli import (
    consolidate_datalake,
    describe_csv,
    describe_excel,
    discovery_ledger,
    download_pmc_oa,
    download_pmc_tar,
    download_url,
    extract_text_semantic,
    get_pmc_summary,
    list_categories,
    preview_csv,
    search_pmc,
    validate_config_file,
    validate_config_str,
)


FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"


def test_list_categories_contains_gene() -> None:
    categories: list[str] = list_categories()
    assert "Gene" in categories


def test_preview_csv_reads_rows() -> None:
    preview: dict[str, list[str] | list[float]] = preview_csv(FIXTURES_DIR / "preview.csv", n_rows=1)

    assert preview == {"gene": ["BRCA1"], "score": [0.91]}


def test_describe_csv_profiles_columns(tmp_path: Path) -> None:
    file = tmp_path / "describe.csv"
    file.write_text("gene,score,count,flag\nBRCA1,0.91,5,true\nTP53,,3,false\n,0.2,,true\n")

    result = describe_csv(file)
    columns = {column["name"]: column for column in result["columns"]}

    assert result["shape"] == {"rows": 3, "columns": 4}
    assert result["schema"] == {"gene": "String", "score": "Float64", "count": "Int64", "flag": "Boolean"}
    assert result["sample_rows"][0] == {"gene": "BRCA1", "score": 0.91, "count": 5, "flag": True}
    assert columns["gene"]["null_count"] == 1
    assert columns["gene"]["statistics"] == {"min_length": 4, "max_length": 5, "mean_length": 4.5}
    assert columns["score"]["statistics"]["min"] == 0.2
    assert columns["score"]["statistics"]["max"] == 0.91
    assert columns["flag"]["statistics"] == {"true_count": 2, "false_count": 1}


def test_describe_excel_profiles_sheet(tmp_path: Path) -> None:
    file = tmp_path / "describe.xlsx"
    pl.DataFrame({"gene": ["BRCA1", "TP53"], "score": [0.91, 0.87]}).write_excel(file, worksheet="Sheet1")

    result = describe_excel(file, "Sheet1")

    assert result["sheet_name"] == "Sheet1"
    assert result["shape"] == {"rows": 2, "columns": 2}
    assert result["schema"] == {"gene": "String", "score": "Float64"}
    assert result["columns"][1]["statistics"]["max"] == 0.91


def test_validate_config_str_accepts_valid_fixture() -> None:
    result = validate_config_str((FIXTURES_DIR / "valid-config.yaml").read_text())

    assert isinstance(result, list)
    assert "section" in result[0]
    assert "error" in result[0]


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
    assert "section" in result[0]
    assert "error" in result[0]


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
    assert result["paper_url"] == "https://pmc.ncbi.nlm.nih.gov/articles/PMC12345/"
    assert result["supplements"] == [
        {
            "filename": "supp1.xlsx",
            "media_type": "application/vnd.ms-excel",
            "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC12345/bin/supp1.xlsx",
        }
    ]


def test_discovery_ledger_round_trip(tmp_path: Path) -> None:
    ledger_path = tmp_path / "ledger.json"

    empty = discovery_ledger("read", ledger_path)
    assert empty["topic"] == ""
    assert empty["entries"] == []
    assert empty["claims"] == {}
    assert empty["version"] == 2

    claim = discovery_ledger("claim", ledger_path, pmc_id=42, agent_name="the-pioneer", run_id="run-1", topic="cancer")
    assert claim["claimed"] is True
    assert claim["claim"]["pmcid"] == 42

    added = discovery_ledger(
        "add",
        ledger_path,
        pmc_id=42,
        status="success",
        summary="worked",
        topic="cancer",
        config_paths=["ROMERO3.yaml", "ROMERO3B.yaml"],
        artifact_root=".ledger/cancer/data/PMC42",
        agent_name="the-pioneer",
        run_id="run-1",
        s3_uri="s3://pmc-oa-opendata/PMC42.1/",
    )
    assert added["added"]["pmcid"] == 42
    assert added["added"]["config_paths"] == ["ROMERO3.yaml", "ROMERO3B.yaml"]
    assert added["added"]["artifact_root"] == ".ledger/cancer/data/PMC42"
    assert added["added"]["paper_url"] == "https://pmc.ncbi.nlm.nih.gov/articles/PMC42/"
    assert added["added"]["s3_uri"] == "s3://pmc-oa-opendata/PMC42.1/"
    assert added["total_entries"] == 1

    check_hit = discovery_ledger("check", ledger_path, pmc_id=42)
    assert check_hit["exists"] is True
    assert check_hit["entry"]["status"] == "success"
    assert check_hit["claimed"] is False

    assert discovery_ledger("check", ledger_path, pmc_id=99) == {
        "exists": False,
        "entry": None,
        "claimed": False,
        "claim": None,
    }

    disk = json.loads(ledger_path.read_text())
    assert disk["topic"] == "cancer"
    assert disk["version"] == 2
    assert disk["entries"][0]["pmcid"] == 42
    assert disk["entries"][0]["config_paths"] == ["ROMERO3.yaml", "ROMERO3B.yaml"]
    assert disk["claims"] == {}


def test_discovery_ledger_read_normalizes_legacy_config_path(tmp_path: Path) -> None:
    ledger_path = tmp_path / "ledger.json"
    ledger_path.write_text(
        json.dumps({"topic": "cancer", "entries": [{"pmcid": 42, "status": "success", "config_path": "ROMERO3.yaml"}]})
    )

    result = discovery_ledger("read", ledger_path)

    assert result["entries"][0]["config_paths"] == ["ROMERO3.yaml"]


def test_discovery_ledger_release_respects_run_ownership(tmp_path: Path) -> None:
    ledger_path = tmp_path / "ledger.json"

    discovery_ledger("claim", ledger_path, pmc_id=42, run_id="run-1")
    denied = discovery_ledger("release", ledger_path, pmc_id=42, run_id="run-2")

    assert denied["released"] is False
    assert "error" in denied

    released = discovery_ledger("release", ledger_path, pmc_id=42, run_id="run-1")
    assert released["released"] is True


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
    assert result["artifact_root"] == str(tmp_path)
    assert result["dest_dir"] == str(tmp_path / "source" / "PMC11370360.2")
    assert result["source_dir"] == str(tmp_path / "source" / "PMC11370360.2")
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


def test_download_pmc_tar_extracts_into_source_and_removes_archive(tmp_path: Path) -> None:
    archive = tmp_path / "fixture.tar"
    source_fixture = tmp_path / "inside.txt"
    source_fixture.write_text("hello")

    with cli.tarfile.open(archive, "w") as tar:
        tar.add(source_fixture, arcname="nested/inside.txt")

    payload = archive.read_bytes()

    class FakeStream:
        status_code = 200
        headers = {"content-disposition": 'attachment; filename="paper.tar"'}

        def __enter__(self) -> "FakeStream":
            return self

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            return None

        def iter_bytes(self):
            yield payload

    with patch.object(cli.httpx, "stream", return_value=FakeStream()):
        result = download_pmc_tar(42, dest_dir=tmp_path / "paper")

    assert result["status"] == "ok"
    assert result["artifact_root"] == str(tmp_path / "paper")
    assert result["source_dir"] == str(tmp_path / "paper" / "source")
    assert result["files"] == ["nested/inside.txt"]
    assert result["cleanup"]["removed"] == [str(tmp_path / "paper" / "raw" / "paper.tar")]
    assert not (tmp_path / "paper" / "raw" / "paper.tar").exists()
    assert (tmp_path / "paper" / "source" / "nested" / "inside.txt").read_text() == "hello"


def test_download_url_writes_into_raw_dir(tmp_path: Path) -> None:
    class FakeResponse:
        headers = {
            "content-disposition": 'attachment; filename="table.tsv"',
            "content-type": "text/tab-separated-values",
        }

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            return None

        def raise_for_status(self) -> None:
            return None

        def iter_bytes(self):
            yield b"a\tb\n1\t2\n"

    with patch.object(cli.httpx, "stream", return_value=FakeResponse()):
        result = download_url("https://example.org/table", dest_dir=tmp_path / "paper")

    assert result["status"] == "ok"
    assert result["artifact_root"] == str(tmp_path / "paper")
    assert result["path"] == str(tmp_path / "paper" / "raw" / "table.tsv")
    assert (tmp_path / "paper" / "raw" / "table.tsv").read_text() == "a\tb\n1\t2\n"


def write_pioneer_yaml(path: Path, local: str, sections: list[dict[str, Any]] | None = None) -> None:
    config: dict[str, Any] = {
        "template": {
            "source": {"kind": "text", "local": local, "url": "https://example.org/x.csv"},
            "statement": {"subject": {"encoding": "A", "method": "column"}, "object": {"encoding": "Gene"}},
            "provenance": {"publication": "PMC42", "contributors": [{"name": "Test", "date": "2026-04-02"}]},
        }
    }
    if sections is not None:
        config["sections"] = sections
    path.write_text(yaml.safe_dump(config, sort_keys=False))


def test_consolidate_datalake_moves_file_and_rewrites_yaml(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts" / "PMC42"
    (artifact_root / "source").mkdir(parents=True)
    src = artifact_root / "source" / "table1.csv"
    src.write_text("gene,score\nBRCA1,0.91\n")

    launch_dir = tmp_path / "launch"
    launch_dir.mkdir()
    yaml_path = launch_dir / "ROMERO3.yaml"
    write_pioneer_yaml(yaml_path, "source/table1.csv")

    result = consolidate_datalake([yaml_path], pmc_id=42, artifact_root=artifact_root, launch_dir=launch_dir)

    assert result["status"] == "ok"
    assert result["datalake_root"] == str(launch_dir / "DATALAKE")

    target = launch_dir / "DATALAKE" / "PMC42_table1.csv"
    assert target.is_file()
    assert target.read_text() == "gene,score\nBRCA1,0.91\n"
    assert not src.exists()

    rewritten = yaml.safe_load(yaml_path.read_text())
    assert rewritten["template"]["source"]["local"] == "./DATALAKE/PMC42_table1.csv"

    assert result["manifest"] == [
        {"config_path": str(yaml_path), "original_path": str(src), "datalake_path": "./DATALAKE/PMC42_table1.csv"}
    ]


def test_consolidate_datalake_dedupes_shared_file_across_yamls(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts" / "PMC7"
    (artifact_root / "source").mkdir(parents=True)
    src = artifact_root / "source" / "shared.csv"
    src.write_text("a,b\n1,2\n")

    launch_dir = tmp_path / "launch"
    launch_dir.mkdir()
    a = launch_dir / "ALPHA.yaml"
    b = launch_dir / "BETA.yaml"
    write_pioneer_yaml(a, "source/shared.csv")
    write_pioneer_yaml(b, "source/shared.csv")

    result = consolidate_datalake([a, b], pmc_id=7, artifact_root=artifact_root, launch_dir=launch_dir)

    assert result["status"] == "ok"
    assert (launch_dir / "DATALAKE" / "PMC7_shared.csv").is_file()
    for cfg in (a, b):
        rewritten = yaml.safe_load(cfg.read_text())
        assert rewritten["template"]["source"]["local"] == "./DATALAKE/PMC7_shared.csv"

    config_paths = sorted(item["config_path"] for item in result["manifest"])
    assert config_paths == sorted([str(a), str(b)])


def test_consolidate_datalake_handles_section_overrides(tmp_path: Path) -> None:
    artifact_root = tmp_path / "PMC9"
    (artifact_root / "source").mkdir(parents=True)
    base = artifact_root / "source" / "base.csv"
    extra = artifact_root / "source" / "extra.csv"
    base.write_text("x\n1\n")
    extra.write_text("y\n2\n")

    launch_dir = tmp_path / "launch"
    launch_dir.mkdir()
    yaml_path = launch_dir / "GAMMA.yaml"
    write_pioneer_yaml(yaml_path, "source/base.csv", sections=[{"source": {"local": "source/extra.csv"}}])

    result = consolidate_datalake([yaml_path], pmc_id=9, artifact_root=artifact_root, launch_dir=launch_dir)

    assert result["status"] == "ok"
    assert (launch_dir / "DATALAKE" / "PMC9_base.csv").is_file()
    assert (launch_dir / "DATALAKE" / "PMC9_extra.csv").is_file()

    rewritten = yaml.safe_load(yaml_path.read_text())
    assert rewritten["template"]["source"]["local"] == "./DATALAKE/PMC9_base.csv"
    assert rewritten["sections"][0]["source"]["local"] == "./DATALAKE/PMC9_extra.csv"


def test_consolidate_datalake_is_idempotent(tmp_path: Path) -> None:
    artifact_root = tmp_path / "PMC1"
    (artifact_root / "source").mkdir(parents=True)
    (artifact_root / "source" / "t.csv").write_text("a\n1\n")

    launch_dir = tmp_path / "launch"
    launch_dir.mkdir()
    yaml_path = launch_dir / "DELTA.yaml"
    write_pioneer_yaml(yaml_path, "source/t.csv")

    first = consolidate_datalake([yaml_path], pmc_id=1, artifact_root=artifact_root, launch_dir=launch_dir)
    assert first["status"] == "ok"

    second = consolidate_datalake([yaml_path], pmc_id=1, artifact_root=artifact_root, launch_dir=launch_dir)
    assert second["status"] == "ok"
    assert second["manifest"][0]["datalake_path"] == "./DATALAKE/PMC1_t.csv"
    target = launch_dir / "DATALAKE" / "PMC1_t.csv"
    assert target.read_text() == "a\n1\n"


def test_consolidate_datalake_collision_with_different_content(tmp_path: Path) -> None:
    artifact_root = tmp_path / "PMC2"
    (artifact_root / "source").mkdir(parents=True)
    src = artifact_root / "source" / "c.csv"
    src.write_text("incoming\n")

    launch_dir = tmp_path / "launch"
    (launch_dir / "DATALAKE").mkdir(parents=True)
    (launch_dir / "DATALAKE" / "PMC2_c.csv").write_text("preexisting different content\n")

    yaml_path = launch_dir / "EPSILON.yaml"
    write_pioneer_yaml(yaml_path, "source/c.csv")

    result = consolidate_datalake([yaml_path], pmc_id=2, artifact_root=artifact_root, launch_dir=launch_dir)

    assert "error" in result
    assert "DATALAKE collision" in result["error"]
    assert src.exists()


def test_consolidate_datalake_missing_source_errors(tmp_path: Path) -> None:
    artifact_root = tmp_path / "PMC3"
    artifact_root.mkdir()
    launch_dir = tmp_path / "launch"
    launch_dir.mkdir()
    yaml_path = launch_dir / "ZETA.yaml"
    write_pioneer_yaml(yaml_path, "source/missing.csv")

    result = consolidate_datalake([yaml_path], pmc_id=3, artifact_root=artifact_root, launch_dir=launch_dir)

    assert "error" in result
    assert "Source file not found" in result["error"]


def test_discovery_ledger_persists_datalake_manifest(tmp_path: Path) -> None:
    ledger_path = tmp_path / "ledger.json"
    manifest = [
        {
            "config_path": "ALPHA.yaml",
            "original_path": "/tmp/PMC42/source/t.csv",
            "datalake_path": "./DATALAKE/PMC42_t.csv",
        }
    ]

    added = discovery_ledger(
        "add",
        ledger_path,
        pmc_id=42,
        status="success",
        summary="ok",
        topic="cancer",
        config_paths=["ALPHA.yaml"],
        artifact_root=".ledger/cancer/data/PMC42",
        agent_name="the-pioneer",
        run_id="run-1",
        datalake_manifest=json.dumps(manifest),
    )
    assert added["added"]["datalake_manifest"] == manifest

    disk = json.loads(ledger_path.read_text())
    assert disk["entries"][0]["datalake_manifest"] == manifest

    reread = discovery_ledger("read", ledger_path)
    assert reread["entries"][0]["datalake_manifest"] == manifest


def test_discovery_ledger_rejects_invalid_datalake_manifest(tmp_path: Path) -> None:
    ledger_path = tmp_path / "ledger.json"
    bad = discovery_ledger(
        "add", ledger_path, pmc_id=42, status="success", topic="cancer", run_id="run-1", datalake_manifest="not json"
    )
    assert "error" in bad
    assert "datalake_manifest" in bad["error"]
