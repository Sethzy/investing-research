"""One accumulating company brief backed by immutable dated entries."""

import html
import re
from pathlib import Path

from .workspace import atomic_text, digest, now, read_json, write_json


def _quote(text):
    # A fence longer than any source fence preserves literal Markdown as evidence.
    fence = "`" * max(3, max((len(x) + 1 for x in re.findall(r"`+", text)), default=3))
    return f"{fence}text\n{text}\n{fence}"


def update(workspace, company_id):
    """Caller holds workspace lock. Exact retries never duplicate entries."""
    company = workspace.company(company_id)
    folder = workspace.root / "companies" / company_id
    ledger = workspace.root / "state/journal" / company_id
    ledger.mkdir(parents=True, exist_ok=True)
    existing = [read_json(p) for p in sorted(ledger.glob("*.json"))]
    for item in existing:
        if digest(item["payload"]) != item["id"]:
            raise ValueError("Journal entry integrity check failed")
    ids = {x["id"] for x in existing}

    def save(payload):
        identity = digest(payload)
        if identity in ids:
            return
        entry = {"id": identity, "appended_at": now(), "payload": payload}
        write_json(ledger / f"{len(existing)+1:08d}-{identity}.json", entry)
        existing.append(entry)
        ids.add(identity)

    captures = workspace.captures()
    runs = sorted((read_json(p) for p in (workspace.root / "state/runs").glob("*.json")),
                  key=lambda r: r["started_at"])
    prior_decisions = {}
    for run in runs:
        if company_id not in run.get("company_ids", []):
            continue
        ops = [o for o in run.get("operations", []) if o.get("company_id") == company_id]
        current_decisions = {d["capture_id"]: d for d in run.get("decisions", [])
                             if d["company_id"] == company_id}
        decisions = {**prior_decisions, **current_decisions}
        capture_ids = sorted({cid for op in ops for cid in op.get("capture_ids", [])} | current_decisions.keys())
        lines = [f"## Run {run['started_at']} / {run['status']}", "",
                 f"Run ID: {run['id']}. Reviewed: {run.get('reviewed_at') or 'pending'}.", "",
                 "### X search coverage", ""]
        for kind, title in [("x", "X"), ("web", "Public web and reports")]:
            selected = [o for o in ops if (o.get("kind") == "x") == (kind == "x")]
            if kind != "x":
                lines += ["### Public web and reports coverage", ""]
            if not selected:
                lines += [f"{title}: not attempted in this run. Coverage gap; not a no-change finding.", ""]
            for op in selected:
                lines += [f"- {op.get('actual_query') or op.get('query') or op.get('url') or 'Source'}: "
                          f"{op.get('status', 'unknown')}. Coverage: {op.get('coverage', {})}", ""]
        lines += ["Search results are bounded and not exhaustive. Captured text may be partial; "
                  "it does not establish full thread, article or media coverage.", ""]
        for error in run.get("errors", []):
            lines += [f"Coverage warning: {error}", ""]
        for cid in capture_ids:
            source = captures.get(cid)
            if not source:
                lines += [f"Missing capture: {cid}", ""]
                continue
            social = source.get("kind") == "x"
            lines += [f"### {'X post' if social else 'Report / web source'}: {source.get('title', cid)}", "",
                      f"[Original source]({source['url']})", "",
                      f"Published: {source.get('published_at') or 'unknown'}. "
                      f"Captured: {source.get('retrieved_at') or source.get('first_seen', 'unknown')}. "
                      f"Completeness: {source.get('completeness', 'unknown')}.", ""]
            if social:
                lines += ["Captured verbatim text (untrusted source content):", "",
                          _quote(source.get("text") or "[No text captured]"), ""]
            for file in source.get("files", []):
                lines += [f"[Retained capture file](../../{file})", ""]
            decision = decisions.get(cid)
            if decision:
                if cid not in current_decisions:
                    lines += ["Analysis carried forward from an earlier reviewed run of this exact capture.", ""]
                lines += [f"Analysis ({decision['verification']}; "
                          f"{'material' if decision['material'] else 'not material'}): "
                          f"{decision['summary']}", "",
                          f"Model impact: {decision['model_impact']}", ""]
            else:
                lines += ["Analysis: review pending; no investment conclusion recorded.", ""]
        save({"kind": "run", "run_id": run["id"], "status": run["status"], "body": "\n".join(lines)})
        prior_decisions.update(current_decisions)

    # Keep dated artifact inventories and readable narratives as immutable snapshots.
    paths = set(folder.glob("models/*/*")) | set(folder.glob("updates/*/*")) | set(folder.glob("funding/*/*"))
    paths |= set(folder.glob("coverage/*/*"))
    paths |= {folder / name for name in ("thesis.md", "research.md", "investment-review.md")}
    if company_id == "asx-mlx":
        paths |= set((workspace.root / "examples/mlx").glob("*"))
    artifacts = []
    for path in sorted(paths):
        if not path.is_file() or path.suffix not in {".md", ".json", ".xlsx", ".svg"}:
            continue
        import hashlib
        artifacts.append({"path": workspace.relative(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                          "text": path.read_text() if path.suffix == ".md" else None})
    if artifacts:
        lines = ["## Research and model artifacts", "",
                 "Inventory appended when artifact content changes. Historical entries are preserved. "
                 "Excel links open the retained detailed models; Markdown model memos follow below.", ""]
        for a in artifacts:
            lines += [f"- [{a['path']}](../../{a['path']}) / SHA256 {a['sha256']}", ""]
        for a in artifacts:
            if a["text"]:
                def rebase(match):
                    dest = match[2]
                    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", dest) or dest.startswith('#'):
                        return match[0]
                    resolved = (workspace.root / a['path']).parent / dest
                    if not resolved.resolve().is_relative_to(workspace.root):
                        return match[1]
                    import os
                    return f"[{match[1]}]({Path(os.path.relpath(resolved, folder)).as_posix()})"
                narrative = re.sub(r'\[([^]]+)\]\(([^)]+)\)', rebase, a['text'])
                lines += [f"### Artifact: {a['path']}", "", narrative, ""]
        save({"kind": "artifacts", "artifacts": artifacts, "body": "\n".join(lines)})
    records = []
    for category in ('facts', 'recommendations'):
        records += [read_json(p) for p in sorted((workspace.root / 'state' / category).glob('*.json'))
                    if read_json(p).get('company_id') == company_id]
    if records:
        lines = ['## Reported facts and investment views', '',
                 'Recorded facts retain their periods and ownership basis. Views and assumptions are '
                 'separate from reported facts. Sources outside collection runs are included here.', '']
        for record in records:
            if 'metric' in record:
                lines += [f"- {record['metric']}: {record['value']} {record['unit']}; "
                          f"period {record['period']}; basis {record['ownership_basis']}; "
                          f"page {record['page']}.", '']
            else:
                lines += [f"### View dated {record.get('as_of')}: {record.get('action')}", '',
                          record.get('thesis', ''), '', f"Horizon: {record.get('horizon')}", '']
                for key in ('counterarguments', 'catalysts', 'entry_conditions', 'invalidation_conditions', 'limitations'):
                    lines += [f"{key.replace('_', ' ').title()}: {item}" for item in record.get(key, [])]
                    lines += ['']
            source_ids = record.get('source_ids', []) + ([record['source_id']] if 'source_id' in record else [])
            for sid in source_ids:
                source = captures.get(sid)
                if source:
                    lines += [f"[Primary evidence]({source['url']})", '']
                    lines += [f"[Retained source](../../{f})" for f in source.get('files', [])]
                    lines += ['']
        save({'kind': 'facts-and-views', 'records': records, 'body': '\n'.join(lines)})
    lines = [f"# {company.name} ({company.exchange}:{company.ticker}) - accumulating brief", "",
             "Entries append in recording order, with original run dates retained. Backfilled entries "
             "are labelled by their append timestamp. Pending and reviewed revisions are both retained. "
             "This is captured evidence and analysis, not a guarantee of complete source coverage.", ""]
    for entry in existing:
        lines += [f"Appended: {entry['appended_at']} | Entry: {entry['id'][:12]}", "",
                  entry["payload"]["body"], "", "---", ""]
    target = folder / "brief.md"
    atomic_text(target, "\n".join(lines))
    return target


def export_pdf(markdown: Path, target: Path):
    """Export entire journal, with exact UTF-8 Markdown attached to the PDF."""
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from pypdf import PdfReader, PdfWriter
    import io

    fonts = [Path('/Library/Fonts/Arial Unicode.ttf'),
             Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
    font = "Helvetica"
    supported = set(range(32, 127)) | {10, 9}
    for path in fonts:
        if path.exists():
            font = "JournalUnicode"
            pdfmetrics.registerFont(TTFont(font, str(path)))
            supported = set(pdfmetrics.getFont(font).face.charToGlyph)
            break
    def safe(value):
        return ''.join(c if ord(c) in supported or c in '\n\t' else f'[U+{ord(c):04X}]' for c in value)
    body = ParagraphStyle('body', fontName=font, fontSize=8.5, leading=12, spaceAfter=6,
                          splitLongWords=True)
    heading = ParagraphStyle('heading', parent=body, fontSize=13, leading=17, spaceBefore=13,
                             textColor=colors.HexColor('#17364D'), keepWithNext=True)
    quote = ParagraphStyle('quote', parent=body, leftIndent=10, rightIndent=8,
                           backColor=colors.HexColor('#F0F5F8'), borderPadding=5)
    story = [Paragraph('Complete accumulated brief. Exact UTF-8 Markdown is attached. '
                       'Unsupported glyphs display as Unicode code points. Links to local artifacts '
                       'require the companion workspace or ZIP.', body)]
    fenced = False
    fence = None
    for line in markdown.read_text().splitlines():
        if re.fullmatch(r'`{3,}(?:text)?', line):
            marker = line.removesuffix('text')
            if not fenced:
                fenced, fence = True, marker
                continue
            if marker == fence:
                fenced = False
                continue
        if not line:
            story.append(Spacer(1,4))
            continue
        style = quote if fenced else heading if line.startswith('#') else body
        text = html.escape(safe(line if fenced else line.lstrip('# ')))
        if not fenced:
            def hyperlink(match):
                dest = match[2]
                if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', dest) and not dest.startswith(('https:', 'http:')):
                    return match[1]
                return f'<link href="{dest}" color="#176D8C">{match[1]}</link>'
            text = re.sub(r'\[([^]]+)\]\(([^)]+)\)', hyperlink, text)
        story.append(Paragraph(text, style))
    stream = io.BytesIO()
    def footer(canvas, doc):
        canvas.setFont('Helvetica',8)
        canvas.drawString(40,22,'Accumulating research brief | Captures may be partial')
        canvas.drawRightString(555,22,str(doc.page))
    SimpleDocTemplate(stream, rightMargin=40, leftMargin=40, topMargin=36, bottomMargin=40,
                      title=markdown.stem+' - complete research journal').build(
                          story,onFirstPage=footer,onLaterPages=footer)
    writer = PdfWriter()
    writer.append(PdfReader(stream))
    writer.add_attachment(markdown.name, markdown.read_bytes())
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('wb') as f:
        writer.write(f)
    return target
