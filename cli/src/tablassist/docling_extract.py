# pyright: reportMissingImports=false
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "docling>=2.84.0",
# ]
# ///

import sys
from pathlib import Path
from typing import Literal

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, ImageFormatOption, PdfFormatOption


def build_converter(ocr: Literal["auto", "off", "on"]) -> DocumentConverter:
    if ocr == "auto":
        return DocumentConverter()

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = ocr == "on"

    format_options = {
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
        InputFormat.IMAGE: ImageFormatOption(pipeline_options=pipeline_options),
    }
    return DocumentConverter(format_options=format_options)


def main() -> int:
    if len(sys.argv) != 4:
        raise SystemExit("Usage: docling_extract.py <file> <markdown|text> <auto|off|on>")

    file = Path(sys.argv[1])
    output_format: Literal["markdown", "text"] = sys.argv[2]  # pyright: ignore[reportAssignmentType]
    ocr: Literal["auto", "off", "on"] = sys.argv[3]  # pyright: ignore[reportAssignmentType]

    converter = build_converter(ocr)
    result = converter.convert(file)

    if output_format == "text":
        sys.stdout.write(result.document.export_to_markdown(strict_text=True))
    else:
        sys.stdout.write(result.document.export_to_markdown())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
