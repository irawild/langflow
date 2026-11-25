# ruff: noqa: INP001
"""Render the production automation plan Markdown into a styled PDF."""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    ListFlowable,
    ListItem,
    LongTable,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    TableStyle,
)

HERE = Path(__file__).parent
SOURCE = HERE / "Plano de Automacao - Esteira de Conteudos.md"
OUTPUT = HERE / "Plano de Automacao - Esteira de Conteudos.pdf"

FONT_CANDIDATES = [
    (
        Path("/System/Library/Fonts/Supplemental"),
        "Arial.ttf",
        "Arial Bold.ttf",
        "Arial Italic.ttf",
        "Arial Bold Italic.ttf",
    ),
    (
        Path("/usr/share/fonts/truetype/dejavu"),
        "DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf",
        "DejaVuSans-Oblique.ttf",
        "DejaVuSans-BoldOblique.ttf",
    ),
]

FONT_REG = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_ITALIC = "Helvetica-Oblique"
FONT_BOLD_ITALIC = "Helvetica-BoldOblique"
for font_dir, regular, bold, italic, bold_italic in FONT_CANDIDATES:
    font_files = [font_dir / name for name in (regular, bold, italic, bold_italic)]
    if all(path.exists() for path in font_files):
        FONT_REG, FONT_BOLD, FONT_ITALIC, FONT_BOLD_ITALIC = (
            "PlanSans",
            "PlanSans-Bold",
            "PlanSans-Italic",
            "PlanSans-BoldItalic",
        )
        for font_name, font_path in zip(
            (FONT_REG, FONT_BOLD, FONT_ITALIC, FONT_BOLD_ITALIC), font_files, strict=True
        ):
            pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
        pdfmetrics.registerFontFamily(
            FONT_REG,
            normal=FONT_REG,
            bold=FONT_BOLD,
            italic=FONT_ITALIC,
            boldItalic=FONT_BOLD_ITALIC,
        )
        break

NAVY = colors.HexColor("#17324D")
TEAL = colors.HexColor("#1F7282")
PALE = colors.HexColor("#EAF2F5")
INK = colors.HexColor("#25313A")
MUTED = colors.HexColor("#65737E")
GRID = colors.HexColor("#CBD5DC")

styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="PlanTitle",
        parent=styles["Title"],
        fontName=FONT_BOLD,
        fontSize=23,
        leading=28,
        textColor=NAVY,
        alignment=TA_LEFT,
        spaceAfter=8 * mm,
    )
)
styles.add(
    ParagraphStyle(
        name="PlanH1",
        parent=styles["Heading1"],
        fontName=FONT_BOLD,
        fontSize=15,
        leading=19,
        textColor=NAVY,
        spaceBefore=5 * mm,
        spaceAfter=2.5 * mm,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        name="PlanH2",
        parent=styles["Heading2"],
        fontName=FONT_BOLD,
        fontSize=11,
        leading=14,
        textColor=TEAL,
        spaceBefore=3.5 * mm,
        spaceAfter=1.5 * mm,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        name="PlanH3",
        parent=styles["Heading3"],
        fontName=FONT_BOLD,
        fontSize=9.5,
        leading=12,
        textColor=NAVY,
        spaceBefore=2.5 * mm,
        spaceAfter=1 * mm,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        name="PlanBody",
        parent=styles["BodyText"],
        fontName=FONT_REG,
        fontSize=8.6,
        leading=12,
        textColor=INK,
        alignment=TA_LEFT,
        spaceAfter=2.2 * mm,
        allowWidows=0,
        allowOrphans=0,
    )
)
styles.add(
    ParagraphStyle(
        name="PlanBullet",
        parent=styles["PlanBody"],
        leftIndent=3 * mm,
        firstLineIndent=0,
        spaceAfter=1.2 * mm,
    )
)
styles.add(
    ParagraphStyle(
        name="PlanTable",
        parent=styles["PlanBody"],
        fontSize=7.1,
        leading=9.1,
        spaceAfter=0,
    )
)
styles.add(
    ParagraphStyle(
        name="PlanTableHeader",
        parent=styles["PlanTable"],
        fontName=FONT_BOLD,
        textColor=colors.white,
    )
)
styles.add(
    ParagraphStyle(
        name="PlanCode",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=7.2,
        leading=9.2,
        textColor=INK,
        backColor=PALE,
        borderColor=GRID,
        borderWidth=0.4,
        borderPadding=6,
        spaceBefore=1 * mm,
        spaceAfter=3 * mm,
    )
)
styles.add(
    ParagraphStyle(
        name="PlanMeta",
        parent=styles["PlanBody"],
        fontSize=9,
        textColor=MUTED,
        spaceAfter=5 * mm,
    )
)


def inline_markup(text: str) -> str:
    """Convert the small inline Markdown subset used in the plan to ReportLab markup."""
    text = html.escape(text, quote=False)
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<link href="\2" color="#1F7282">\1</link>',
        text,
    )
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r'<font name="Courier" size="7.6">\1</font>', text)
    return re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def make_table(lines: list[str], width: float):
    raw_rows = [split_table_row(line) for line in lines]
    rows = [row for row in raw_rows if not all(re.fullmatch(r"\s*:?-{3,}:?\s*", cell) for cell in row)]
    if not rows:
        return Spacer(1, 1)

    column_count = max(len(row) for row in rows)
    formatted = []
    for row_index, source_row in enumerate(rows):
        row = source_row + [""] * (column_count - len(source_row))
        style = styles["PlanTableHeader"] if row_index == 0 else styles["PlanTable"]
        formatted.append([Paragraph(inline_markup(cell), style) for cell in row])

    table = LongTable(
        formatted,
        colWidths=[width / column_count] * column_count,
        repeatRows=1,
        hAlign="LEFT",
        splitByRow=1,
    )
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    commands.extend(
        ("BACKGROUND", (0, row_index), (-1, row_index), colors.HexColor("#F5F8FA"))
        for row_index in range(1, len(formatted))
        if row_index % 2 == 0
    )
    table.setStyle(TableStyle(commands))
    return KeepTogether([Spacer(1, 1.5 * mm), table, Spacer(1, 2.5 * mm)])


def render_markdown(source: str, width: float):
    lines = source.splitlines()
    story = []
    index = 0
    while index < len(lines):
        raw = lines[index].rstrip()
        stripped = raw.strip()
        if stripped == "<!-- pagebreak -->":
            story.append(PageBreak())
            index += 1
            continue
        if not stripped or stripped == "---":
            index += 1
            continue

        if stripped.startswith("```"):
            index += 1
            code_lines = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            index += 1
            story.append(Preformatted("\n".join(code_lines), styles["PlanCode"], maxLineLength=100))
            continue

        if stripped.startswith("|"):
            table_lines = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index])
                index += 1
            story.append(make_table(table_lines, width))
            continue

        heading = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if heading:
            level = len(heading.group(1))
            style = {1: styles["PlanTitle"], 2: styles["PlanH1"], 3: styles["PlanH2"]}[level]
            story.append(Paragraph(inline_markup(heading.group(2)), style))
            index += 1
            continue

        if stripped.startswith("> "):
            quote = stripped[2:]
            quote_style = ParagraphStyle(
                "PlanCallout",
                parent=styles["PlanBody"],
                backColor=PALE,
                borderColor=TEAL,
                borderWidth=1,
                borderPadding=7,
                leftIndent=4 * mm,
                rightIndent=4 * mm,
                spaceBefore=2 * mm,
                spaceAfter=3 * mm,
            )
            story.append(Paragraph(inline_markup(quote), quote_style))
            index += 1
            continue

        if re.match(r"^[-*]\s+", stripped):
            items = []
            while index < len(lines) and re.match(r"^\s*[-*]\s+", lines[index]):
                item_text = re.sub(r"^\s*[-*]\s+", "", lines[index].strip())
                items.append(ListItem(Paragraph(inline_markup(item_text), styles["PlanBullet"])))
                index += 1
            story.append(
                ListFlowable(
                    items,
                    bulletType="bullet",
                    start="circle",
                    leftIndent=11,
                    bulletFontName=FONT_REG,
                    bulletFontSize=6,
                    bulletColor=TEAL,
                    spaceAfter=2 * mm,
                )
            )
            continue

        numbered = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if numbered:
            items = []
            while index < len(lines):
                match = re.match(r"^\s*\d+\.\s+(.*)$", lines[index].strip())
                if not match:
                    break
                items.append(ListItem(Paragraph(inline_markup(match.group(1)), styles["PlanBullet"])))
                index += 1
            story.append(
                ListFlowable(
                    items,
                    bulletType="1",
                    leftIndent=15,
                    bulletFontName=FONT_REG,
                    bulletFontSize=8,
                    bulletColor=TEAL,
                    spaceAfter=2 * mm,
                )
            )
            continue

        paragraph_lines = [stripped]
        index += 1
        while index < len(lines):
            next_line = lines[index].strip()
            if (
                not next_line
                or next_line == "---"
                or next_line.startswith(("#", "|", "```", "> "))
                or re.match(r"^[-*]\s+", next_line)
                or re.match(r"^\d+\.\s+", next_line)
            ):
                break
            paragraph_lines.append(next_line)
            index += 1

        paragraph_text = " ".join(paragraph_lines)
        if paragraph_text.startswith(("**Fábrica de Conteúdo", "**Fábrica de Conteudo")):
            story.append(Paragraph(inline_markup(paragraph_text), styles["PlanMeta"]))
        else:
            story.append(Paragraph(inline_markup(paragraph_text), styles["PlanBody"]))

    return story


def draw_page(canvas, document):
    canvas.saveState()
    page_width, page_height = A4
    if document.page > 1:
        canvas.setStrokeColor(GRID)
        canvas.setLineWidth(0.5)
        canvas.line(16 * mm, page_height - 13 * mm, page_width - 16 * mm, page_height - 13 * mm)
        canvas.setFont(FONT_REG, 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(16 * mm, page_height - 10 * mm, "PLANO DE AUTOMAÇÃO | FÁBRICA DE CONTEÚDO FINANCEIRO")
    canvas.setStrokeColor(GRID)
    canvas.setLineWidth(0.5)
    canvas.line(16 * mm, 13 * mm, page_width - 16 * mm, 13 * mm)
    canvas.setFont(FONT_REG, 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(16 * mm, 8.5 * mm, "Estimativas e requisitos verificados em 24/11/2026")
    canvas.drawRightString(page_width - 16 * mm, 8.5 * mm, f"Página {document.page}")
    canvas.restoreState()


def main():
    text = SOURCE.read_text(encoding="utf-8")
    document = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=19 * mm,
        bottomMargin=18 * mm,
        title="Plano de Automação da Esteira de Conteúdo",
        author="Langflow — Fábrica de Conteúdo Financeiro",
        subject="Plano técnico, operacional e de custos para geração e publicação de conteúdo",
    )
    usable_width = A4[0] - document.leftMargin - document.rightMargin
    story = render_markdown(text, usable_width)
    document.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    print(f"PDF salvo: {OUTPUT}")  # noqa: T201
    return OUTPUT


if __name__ == "__main__":
    main()
