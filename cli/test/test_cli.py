from pathlib import Path
from typing import Any

import tablassist.cli as cli
from tablassist.cli import (
    extract_text_semantic,
    list_categories,
    preview_csv,
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
