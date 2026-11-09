"""Source-bound Word/PDF exports; portable checks do not rerasterize fonts."""

import argparse
import hashlib
import io
import json
import platform
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
import zlib
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from docx import Document
from docx.shared import Inches, Pt
from PIL import Image, ImageColor, ImageDraw, ImageFont, features
from PIL import __version__ as PILLOW_VERSION
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image as PDFImage
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("research/VALIDATED_RESEARCH_REPORT.md")
WORD = Path("research/VALIDATED_RESEARCH_REPORT.docx")
FINAL = Path("submission/final-review")
FONT = Path(__file__).resolve().parents[1] / "research/review_resolution/fonts/NotoSansSC-report-subset.ttf"
SCRIPT = Path(__file__).resolve()
LOCK = SCRIPT.parents[1] / "uv.lock"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def plain(text):
    text = re.sub(r"!?\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text.replace("*", "").replace("`", "")


def blocks(text):
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):
            code = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            yield "code", "\n".join(code)
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            yield "table", rows
            continue
        elif re.match(r"!\[.*\]\(.*\)$", line):
            match = re.match(r"!\[([^]]*)\]\(([^)]+)\)", line)
            yield "figure", (match[1], (ROOT / SOURCE.parent / match[2]).resolve())
        elif line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            yield "heading", (level, line[level:].strip())
        else:
            paragraph = [line]
            i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "|", "![", "```", "- ")):
                paragraph.append(lines[i])
                i += 1
            yield "paragraph", " ".join(paragraph)
            continue
        i += 1


def png_from_svg(data):
    element = ET.fromstring(data)
    width, height = int(element.attrib["width"]), int(element.attrib["height"])
    image = Image.new("RGB", (width, height), "white")
    drawing = ImageDraw.Draw(image)
    for child in element.iter():
        tag = child.tag.rsplit("}", 1)[-1]
        attrs = child.attrib
        if tag == "rect":
            x, y = float(attrs.get("x", 0)), float(attrs.get("y", 0))
            w = width if attrs["width"] == "100%" else float(attrs["width"])
            h = height if attrs["height"] == "100%" else float(attrs["height"])
            fill = ImageColor.getrgb(attrs.get("fill", "black"))
            drawing.rectangle([x, y, x + w, y + h], fill=fill)
        elif tag == "text":
            font = ImageFont.load_default(size=float(attrs.get("font-size", 14)))
            anchor = {"start": "ls", "middle": "ms", "end": "rs"}[attrs.get("text-anchor", "start")]
            drawing.text((float(attrs["x"]), float(attrs["y"])), child.text or "", font=font,
                         fill=attrs.get("fill", "black"), anchor=anchor)
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def normalize_docx(data):
    source, target = io.BytesIO(data), io.BytesIO()
    with zipfile.ZipFile(source) as original, zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as result:
        for name in sorted(original.namelist()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            result.writestr(info, original.read(name))
    return target.getvalue()


def render_inputs():
    inputs = {"renderer_script": sha(SCRIPT.read_bytes()),
              "dependency_lock": sha(LOCK.read_bytes()),
              "embedded_cjk_font": sha(FONT.read_bytes()),
              "canonical_markdown": sha((ROOT / SOURCE).read_bytes())}
    for kind, value in blocks((ROOT / SOURCE).read_text()):
        if kind == "figure":
            _, path = value
            inputs["svg:" + str(path.relative_to(ROOT))] = sha(path.read_bytes())
    return inputs


def verify_exports():
    """Verify published bytes AND every input, plus Word content/image joins.

    FreeType/zlib builds can produce different PNG/PDF bytes on different OSes.
    This never silently substitutes Linux renders for the reviewed published ones.
    Same-environment byte reproducibility is tested independently.
    """
    metadata = json.loads((ROOT / "results/WORD_REPORT_EXPORT.json").read_text())
    if (metadata.get("source_markdown") != str(SOURCE) or metadata.get("word_file") != str(WORD)
            or metadata.get("pdf_file") != str(FINAL / "Authority_Language_Final.pdf")):
        raise ValueError("unexpected_export_paths")
    if metadata.get("renderer_inputs_sha256") != render_inputs():
        raise ValueError("missing_or_stale_renderer_inputs")
    if metadata.get("source_sha256") != sha((ROOT / SOURCE).read_bytes()):
        raise ValueError("stale_export_source")
    parsed = list(blocks((ROOT / SOURCE).read_text()))
    images = [value[1].with_suffix(".png").relative_to(ROOT) for kind, value in parsed if kind == "figure"]
    expected_paths = {WORD, FINAL / "Authority_Language_Final.docx", FINAL / "Authority_Language_Final.pdf", *images}
    recorded = metadata.get("generated_sha256", {})
    if set(recorded) != {str(p) for p in expected_paths}:
        raise ValueError("missing_or_unexpected_export_artifacts")
    for name, expected in recorded.items():
        path = ROOT / name
        if not path.exists() or sha(path.read_bytes()) != expected:
            raise ValueError("missing_or_modified_export: " + name)
    if metadata.get("word_sha256") != recorded[str(WORD)] or metadata.get("pdf_sha256") != recorded[str(FINAL / "Authority_Language_Final.pdf")]:
        raise ValueError("inconsistent_export_manifest")
    if (ROOT / WORD).read_bytes() != (ROOT / FINAL / "Authority_Language_Final.docx").read_bytes():
        raise ValueError("word_copies_disagree")
    expected_text = []
    for kind, value in parsed:
        if kind in ("heading", "figure"):
            expected_text.append(plain(value[1] if kind == "heading" else value[0]))
        elif kind == "table":
            expected_text.extend(plain(cell) for row in value for cell in row)
        elif kind == "code":
            expected_text.extend(value.splitlines())
        else:
            expected_text.append(plain(value))
    with zipfile.ZipFile(ROOT / WORD) as archive:
        xml = ET.fromstring(archive.read("word/document.xml"))
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        actual = ["".join(node.text or "" for node in paragraph.iter(ns + "t")) for paragraph in xml.iter(ns + "p")]
        if [x for x in actual if x] != [x for x in expected_text if x]:
            raise ValueError("word_content_differs_from_canonical_markdown")
        embedded = {sha(archive.read(name)) for name in archive.namelist() if name.startswith("word/media/")}
        if embedded != {sha((ROOT / path).read_bytes()) for path in images}:
            raise ValueError("word_figures_differ_from_published_pngs")
    if not (ROOT / FINAL / "Authority_Language_Final.pdf").read_bytes().startswith(b"%PDF"):
        raise ValueError("invalid_pdf_export")
    pdf = PdfReader(ROOT / FINAL / "Authority_Language_Final.pdf")
    footer = "Authority-language research | evidence-backed post-review report"
    pages = [re.sub(re.escape(footer) + r"\s*" + str(index + 1) + r"\b", "", page.extract_text() or "")
             for index, page in enumerate(pdf.pages)]

    def compact(text):
        return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))

    pdf_text, cursor = compact("\n".join(pages)), 0
    for part in expected_text:
        needle = compact(part)
        if not needle:
            continue
        found = pdf_text.find(needle, cursor)
        if found < 0:
            raise ValueError("pdf_content_differs_from_canonical_markdown: " + part[:60])
        cursor = found + len(needle)
    return len(expected_paths) + 1


def build_exports():
    markdown = (ROOT / SOURCE).read_text()
    parsed = list(blocks(markdown))
    output = {}
    for kind, value in parsed:
        if kind == "figure":
            _, path = value
            output[path.with_suffix(".png").relative_to(ROOT)] = png_from_svg(path.read_bytes())
    document = Document()
    section = document.sections[0]
    section.top_margin = section.bottom_margin = Inches(.65)
    section.left_margin = section.right_margin = Inches(.65)
    document.styles["Normal"].font.name = "Calibri"
    document.styles["Normal"].font.size = Pt(9)
    document.core_properties.title = "Record provenance, stale evidence and budget relay"
    document.core_properties.author = "Author confirmation required"
    document.core_properties.created = document.core_properties.modified = datetime(2026, 11, 9, tzinfo=timezone.utc)
    styles = getSampleStyleSheet()
    pdfmetrics.registerFont(TTFont("ReportCJK", str(FONT)))
    for level in (1, 2, 3):
        styles[f"Heading{level}"].keepWithNext = True
    styles.add(ParagraphStyle("Research", fontName="Helvetica", fontSize=9, leading=12,
                              spaceAfter=7, alignment=TA_LEFT, splitLongWords=True))
    styles.add(ParagraphStyle("ResearchCell", fontName="Helvetica", fontSize=7, leading=9,
                              splitLongWords=True))
    story, table_rows = [], []
    pdf_stream = io.BytesIO()
    pdf = SimpleDocTemplate(pdf_stream, pagesize=(210 * mm, 297 * mm),
                            leftMargin=16 * mm, rightMargin=16 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm,
                            invariant=1, title=document.core_properties.title,
                            author="Author confirmation required")

    def para(text, cell=False):
        rendered = escape(plain(text))
        cjk = re.findall(r"[\u3400-\u9fff]", rendered)
        if any(char not in "费用" for char in cjk):
            raise ValueError("Extend the licensed report font subset for additional CJK characters")
        rendered = re.sub(r"[\u3400-\u9fff]+", r'<font name="ReportCJK">\g<0></font>', rendered)
        return Paragraph(rendered, styles["ResearchCell" if cell else "Research"])

    references = False
    for kind, value in parsed:
        if kind == "heading":
            level, title = value
            references = title == "References"
            document.add_heading(plain(title), level=min(level, 3))
            story.append(Paragraph(escape(plain(title)), styles[f"Heading{min(level, 3)}"]))
        elif kind == "figure":
            caption, path = value
            image_bytes = output[path.with_suffix(".png").relative_to(ROOT)]
            document.add_picture(io.BytesIO(image_bytes), width=Inches(6.9))
            document.add_paragraph(caption, style="Caption")
            image = Image.open(io.BytesIO(image_bytes))
            w = 176 * mm
            story += [PDFImage(io.BytesIO(image_bytes), width=w, height=w * image.height / image.width),
                      para(caption), Spacer(1, 5)]
        elif kind == "table":
            table_rows.append(len(value))
            cols = len(value[0])
            if any(len(row) != cols for row in value):
                raise ValueError("inconsistent_markdown_table_columns")
            table = document.add_table(rows=0, cols=cols)
            table.style = "Light Shading Accent 1"
            for row in value:
                cells = table.add_row().cells
                for cell, text in zip(cells, row):
                    cell.text = plain(text)
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.font.size = Pt(8)
            pdf_table = Table([[para(cell, True) for cell in row] for row in value],
                              colWidths=[176 * mm / cols] * cols, repeatRows=1, hAlign="LEFT")
            pdf_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6efec")),
                ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#c5cfce")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]))
            story += [pdf_table, Spacer(1, 9)]
        elif kind == "code":
            for line in value.splitlines():
                document.add_paragraph(line, style="No Spacing")
                story.append(para(line))
        else:
            document.add_paragraph(plain(value))
            story.append(KeepTogether([para(value)]) if references else para(value))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawString(16 * mm, 10 * mm, "Authority-language research | evidence-backed post-review report")
        canvas.drawRightString(194 * mm, 10 * mm, str(doc.page))
        canvas.restoreState()

    pdf.build(story, onFirstPage=footer, onLaterPages=footer)
    word_stream = io.BytesIO()
    document.save(word_stream)
    word_bytes = normalize_docx(word_stream.getvalue())
    output[WORD] = word_bytes
    output[FINAL / "Authority_Language_Final.docx"] = word_bytes
    output[FINAL / "Authority_Language_Final.pdf"] = pdf_stream.getvalue()
    metadata = {"source_markdown": str(SOURCE), "source_sha256": sha((ROOT / SOURCE).read_bytes()),
                "word_file": str(WORD), "word_sha256": sha(word_bytes),
                "pdf_file": str(FINAL / "Authority_Language_Final.pdf"),
                "pdf_sha256": sha(pdf_stream.getvalue()), "table_rows_including_headers": table_rows,
                "embedded_cjk_font_sha256": sha(FONT.read_bytes()),
                "renderer_inputs_sha256": render_inputs(),
                "verification_contract": "Recorded artifact hashes, renderer/dependency/font/SVG/source hashes and Word text/image joins; not cross-OS raster byte equivalence",
                "render_environment": {"platform": platform.system(), "python": platform.python_version(),
                                       "pillow": PILLOW_VERSION, "freetype": features.version("freetype2"),
                                       "zlib": zlib.ZLIB_VERSION},
                "visual_review": "Export generation is not visual or human author review; see hash-bound EXPORT_REVIEW.json if present",
                "historical_word_reports": "Original canonical report/export archived at research/review_resolution/archive/1dcf401; other originals unchanged",
                "generated_sha256": {str(path): sha(content) for path, content in output.items()}}
    output[Path("results/WORD_REPORT_EXPORT.json")] = (json.dumps(metadata, indent=2) + "\n").encode()
    return output


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    if args.check:
        count = verify_exports()
        print(json.dumps({"mode": "check", "artifacts": count, "source": str(SOURCE), "raster_regeneration_required": False}))
        return
    outputs = build_exports()
    for path, data in outputs.items():
        target = ROOT / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    print(json.dumps({"mode": "check" if args.check else "write", "artifacts": len(outputs), "source": str(SOURCE)}))


if __name__ == "__main__":
    main()
