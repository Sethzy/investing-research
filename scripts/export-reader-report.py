"""Render authored reader Markdown as a clean PDF, without attaching technical history."""

import argparse
import html
import re
from pathlib import Path
from urllib.parse import urlsplit

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def export(source, output):
    text = source.read_text()
    if "```" in text:
        raise ValueError("Reader reports must contain finished prose, not code or diagram source.")
    if output.exists():
        raise ValueError("Choose a new output path to preserve the earlier reader edition.")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Reader", fontName="Helvetica", fontSize=11, leading=16, spaceAfter=11))
    styles.add(ParagraphStyle(name="Cell", fontName="Helvetica", fontSize=9.3, leading=13))
    for name in ("Heading1", "Heading2", "Heading3"):
        styles[name].textColor = colors.HexColor("#17364D")
        styles[name].spaceAfter = 12

    def paragraph(value, style="Reader"):
        for old, new in [("’", "'"), ("“", '"'), ("”", '"'), ("–", "-"), ("—", " - "), ("×", " x "), ("→", " > ")]:
            value = value.replace(old, new)
        value = html.escape(value)

        def link(match):
            label, destination = match.groups()
            if urlsplit(html.unescape(destination)).scheme not in ("", "https", "http"):
                return label
            return f'<link href="{destination}" color="#087C86">{label}</link>'

        value = re.sub(r"\[([^]]+)\]\(([^)]+)\)", link, value)
        value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
        return Paragraph(value, styles[style])

    story = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        index += 1
        if not line:
            continue
        if line == "<!-- pagebreak -->":
            story.append(PageBreak())
        elif line.startswith("|"):
            rows = [line]
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append(lines[index].strip())
                index += 1
            data = []
            for row in rows:
                cells = [c.strip() for c in row.strip("|").split("|")]
                if all(re.fullmatch(r"[:\- ]+", c) for c in cells):
                    continue
                data.append([paragraph(c, "Cell") for c in cells])
            count = len(data[0])
            width = A4[0] - 96
            weights = {2: [0.32, 0.68], 3: [0.46, 0.27, 0.27]}.get(count, [1 / count] * count)
            table = Table(data, colWidths=[width * w for w in weights], repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCE9EF")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F3F7F9"), colors.white]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.extend([table, Spacer(1, 12)])
        elif line.startswith("#"):
            level = min(3, len(line) - len(line.lstrip("#")))
            story.append(paragraph(line.lstrip("# "), f"Heading{level}"))
        else:
            story.append(paragraph(line))

    def footer(canvas, document):
        canvas.setStrokeColor(colors.HexColor("#C8D9E1"))
        canvas.line(48, 38, A4[0] - 48, 38)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#536774"))
        canvas.drawString(48, 25, "INVESTMENT REVIEW")
        canvas.drawRightString(A4[0] - 48, 25, str(document.page))

    output.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(output), pagesize=A4, leftMargin=48, rightMargin=48,
                      topMargin=42, bottomMargin=54, title=lines[0].lstrip("# ")).build(
                          story, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    export(args.source, args.output)
    print(args.output)
