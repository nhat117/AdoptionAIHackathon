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


@pytest.mark.parametrize("tamper", [
    None, "source", "svg", "png", "pdf", "manifest", "word_semantics", "pdf_semantics"
])
def test_portable_export_verification_is_source_bound_not_raster_byte_bound(
    tmp_path, tamper
):
    pytest.importorskip("docx")
    pytest.importorskip("reportlab")
    pytest.importorskip("PIL")
    module = runpy.run_path(str(ROOT / "scripts/export_review_report.py"))
    build, verify = module["build_exports"], module["verify_exports"]
    build.__globals__["ROOT"] = tmp_path
    source = tmp_path / "research/VALIDATED_RESEARCH_REPORT.md"
    source.parent.mkdir()
    svg = tmp_path / "figure.svg"
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="60">'
                   '<rect width="100%" height="100%" fill="white"/></svg>')
    source.write_text("# Test\n\n| Count | Value |\n|---|---|\n| n | 7 |\n\n"
                      "![Test figure](../figure.svg)\n")
    outputs = build()
    for path, data in outputs.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def no_rasterization(*args):
        raise AssertionError("Portable checks must not match host rasterizers")

    build.__globals__["png_from_svg"] = no_rasterization
    if tamper is None:
        assert verify() == len(outputs)
        return
    if tamper == "source":
        source.write_text(source.read_text() + "\nChanged results.\n")
    elif tamper == "svg":
        svg.write_text(svg.read_text() + "\n")
    elif tamper == "png":
        svg.with_suffix(".png").write_bytes(b"changed")
    elif tamper == "pdf":
        pdf = tmp_path / "submission/final-review/Authority_Language_Final.pdf"
        pdf.write_bytes(b"changed")
    elif tamper in ("word_semantics", "pdf_semantics"):
        import hashlib
        import json

        manifest = tmp_path / "results/WORD_REPORT_EXPORT.json"
        metadata = json.loads(manifest.read_text())
        if tamper == "word_semantics":
            from docx import Document

            word = tmp_path / "research/VALIDATED_RESEARCH_REPORT.docx"
            doc = Document(word)
            doc.paragraphs[0].text = "Invented result"
            doc.save(word)
            data = word.read_bytes()
            copy = tmp_path / "submission/final-review/Authority_Language_Final.docx"
            copy.write_bytes(data)
            digest = hashlib.sha256(data).hexdigest()
            metadata["word_sha256"] = digest
            for name in ("research/VALIDATED_RESEARCH_REPORT.docx",
                         "submission/final-review/Authority_Language_Final.docx"):
                metadata["generated_sha256"][name] = digest
        else:
            from reportlab.pdfgen.canvas import Canvas

            pdf = tmp_path / "submission/final-review/Authority_Language_Final.pdf"
            canvas = Canvas(str(pdf))
            canvas.drawString(50, 700, "Invented result")
            canvas.save()
            digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
            metadata["pdf_sha256"] = digest
            name = "submission/final-review/Authority_Language_Final.pdf"
            metadata["generated_sha256"][name] = digest
        manifest.write_text(json.dumps(metadata))
    else:
        (tmp_path / "results/WORD_REPORT_EXPORT.json").write_text("{}")
    with pytest.raises(ValueError):
        verify()
