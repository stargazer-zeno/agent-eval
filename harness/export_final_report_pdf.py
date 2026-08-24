"""Render the leader-facing GameVisualFix final Markdown report as a checked PDF."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


FONT_PATH = Path(r"C:\Windows\Fonts\msyh.ttc")


def clean_inline(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    return html.escape(text.replace("`", "").replace("**", ""))


def register_font() -> str:
    if not FONT_PATH.is_file():
        raise FileNotFoundError(f"Chinese report font not found: {FONT_PATH}")
    font_name = "MicrosoftYaHei"
    try:
        pdfmetrics.registerFont(TTFont(font_name, str(FONT_PATH), subfontIndex=0))
    except TypeError:
        pdfmetrics.registerFont(TTFont(font_name, str(FONT_PATH)))
    return font_name


def build_styles(font_name: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("GVFTitle", parent=base["Title"], fontName=font_name, fontSize=20, leading=27, alignment=TA_CENTER, spaceAfter=10),
        "h1": ParagraphStyle("GVFH1", parent=base["Heading1"], fontName=font_name, fontSize=15, leading=21, spaceBefore=12, spaceAfter=7),
        "h2": ParagraphStyle("GVFH2", parent=base["Heading2"], fontName=font_name, fontSize=12, leading=17, spaceBefore=9, spaceAfter=5),
        "body": ParagraphStyle("GVFBody", parent=base["BodyText"], fontName=font_name, fontSize=9.3, leading=15, alignment=TA_LEFT, spaceAfter=5),
        "bullet": ParagraphStyle("GVFBullet", parent=base["BodyText"], fontName=font_name, fontSize=9.3, leading=14, leftIndent=13, firstLineIndent=-10, spaceAfter=3),
        "table": ParagraphStyle("GVFTable", parent=base["BodyText"], fontName=font_name, fontSize=7.1, leading=9.2),
        "code": ParagraphStyle("GVFCode", parent=base["Code"], fontName=font_name, fontSize=7.6, leading=10.5, backColor=colors.HexColor("#f4f6f8"), borderPadding=5),
    }


def markdown_story(markdown: str, styles: dict[str, ParagraphStyle]) -> list:
    story: list = []
    lines = markdown.splitlines()
    index, in_code, code_lines = 0, False, []

    def emit_code() -> None:
        if code_lines:
            story.append(Paragraph("<br/>".join(html.escape(line) for line in code_lines), styles["code"]))
            story.append(Spacer(1, 4))
            code_lines.clear()

    while index < len(lines):
        line = lines[index]
        if line.strip().startswith("```"):
            if in_code:
                emit_code()
            in_code = not in_code
            index += 1
            continue
        if in_code:
            code_lines.append(line)
            index += 1
            continue
        if not line.strip():
            index += 1
            continue
        if line.startswith("| "):
            table_lines = []
            while index < len(lines) and lines[index].startswith("|"):
                table_lines.append(lines[index])
                index += 1
            raw_rows = [row.strip().strip("|").split("|") for row in table_lines]
            rows = [raw_rows[0]] + [row for row in raw_rows[2:] if row]
            data = [[Paragraph(clean_inline(cell.strip()), styles["table"]) for cell in row] for row in rows]
            col_count = max(len(row) for row in data)
            for row in data:
                row.extend([Paragraph("", styles["table"])] * (col_count - len(row)))
            width = 184 * mm
            table = Table(data, colWidths=[width / col_count] * col_count, repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, -1), "MicrosoftYaHei"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9e8f5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#102a43")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#a9b9c6")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.extend([table, Spacer(1, 7)])
            continue
        if line.startswith("# "):
            story.append(Paragraph(clean_inline(line[2:]), styles["title"]))
        elif line.startswith("## "):
            story.append(Paragraph(clean_inline(line[3:]), styles["h1"]))
        elif line.startswith("### "):
            story.append(Paragraph(clean_inline(line[4:]), styles["h2"]))
        elif re.match(r"^[-*] ", line):
            story.append(Paragraph("• " + clean_inline(line[2:]), styles["bullet"]))
        elif re.match(r"^\d+\. ", line):
            story.append(Paragraph(clean_inline(line), styles["bullet"]))
        else:
            story.append(Paragraph(clean_inline(line.rstrip("  ")), styles["body"]))
        index += 1
    if in_code:
        raise ValueError("Unclosed Markdown code fence")
    return story


def add_page_number(canvas, doc) -> None:  # type: ignore[no-untyped-def]
    canvas.saveState()
    canvas.setFont("MicrosoftYaHei", 8)
    canvas.setFillColor(colors.HexColor("#52616b"))
    canvas.drawString(16 * mm, 11 * mm, "GameVisualFix v3 — Seed Full-Trace Delivery")
    canvas.drawRightString(194 * mm, 11 * mm, f"Page {doc.page}")
    canvas.restoreState()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    font_name = register_font()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(str(args.output), pagesize=A4, rightMargin=13 * mm, leftMargin=13 * mm, topMargin=15 * mm, bottomMargin=18 * mm, title="GameVisualFix 项目最终汇报", author="GameVisualFix")
    document.build(markdown_story(args.input.read_text(encoding="utf-8"), build_styles(font_name)), onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
