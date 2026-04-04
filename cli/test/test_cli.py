from pathlib import Path

from tablassist.cli import list_categories, preview_csv, validate_config_file, validate_config_str, validate_section_str


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
