"""Report bytes are reproducible and derived from the canonical source."""

import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_export_is_deterministic_and_source_bound(tmp_path):
    pytest.importorskip("docx")
    pytest.importorskip("reportlab")
    pytest.importorskip("PIL")
    module = runpy.run_path(str(ROOT / "scripts/export_review_report.py"))
    build = module["build_exports"]
    build.__globals__["ROOT"] = tmp_path
    source = tmp_path / "research/VALIDATED_RESEARCH_REPORT.md"
    source.parent.mkdir()
    source.write_text(
        "# Fixture report\n\nNot a model result.\n\n| A | B |\n|---|---|\n| 1 | 2 |\n"
    )
    first = build()
    second = build()
    assert first == second
    pdf = Path("submission/final-review/Authority_Language_Final.pdf")
    assert first[pdf].startswith(b"%PDF")
    source.write_text(source.read_text() + "\nChanged evidence summary.\n")
    third = build()
    assert third != first


def test_svg_raster_export_contains_generated_chart():
    image_module = pytest.importorskip("PIL.Image")
    pytest.importorskip("docx")
    pytest.importorskip("reportlab")
    import io

    module = runpy.run_path(str(ROOT / "scripts/export_review_report.py"))
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="60">'
        '<rect width="100%" height="100%" fill="white"/>'
        '<rect x="10" y="10" width="20" height="20" fill="#277b71"/>'
        '<text x="10" y="50" font-size="12">Fixture</text></svg>'
    )
    rendered = module["png_from_svg"](svg)
    image = image_module.open(io.BytesIO(rendered))
    assert image.size == (100, 60)
    assert image.getpixel((15, 15)) == (39, 123, 113)
