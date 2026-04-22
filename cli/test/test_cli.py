import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import tablassist.cli as cli
from tablassist.cli import (
    discovery_ledger,
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


def test_search_pmc_handles_no_results(monkeypatch: Any) -> None:
    def fake_json_response(url: str, params: dict[str, Any]) -> dict[str, Any]:
        return {"esearchresult": {"count": "0", "idlist": []}}

    monkeypatch.setattr(cli, "get_json_response", fake_json_response)

    assert search_pmc("nothing") == {"count": 0, "papers": []}


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
        config_path="cancer/PMC42/config.yaml",
    )
    assert added["added"]["pmcid"] == 42
    assert added["added"]["config_path"] == "cancer/PMC42/config.yaml"
    assert added["total_entries"] == 1

    check_hit = discovery_ledger("check", ledger_path, pmc_id=42)
    assert check_hit["exists"] is True
    assert check_hit["entry"]["status"] == "success"

    assert discovery_ledger("check", ledger_path, pmc_id=99) == {"exists": False, "entry": None}

    disk = json.loads(ledger_path.read_text())
    assert disk["topic"] == "cancer"
    assert disk["entries"][0]["pmcid"] == 42


def test_discovery_ledger_add_requires_fields(tmp_path: Path) -> None:
    ledger_path = tmp_path / "ledger.json"
    result = discovery_ledger("add", ledger_path, pmc_id=None, status="success")
    assert "error" in result
