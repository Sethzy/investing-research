"""Rebuild readable reports from versioned evidence and explicit agent decisions."""

import os
from pathlib import Path

from .contracts import Fact, Recommendation
from .workspace import Workspace, atomic_text, digest, now, read_json, write_json


def add_facts(workspace: Workspace, facts: list[Fact]) -> list[str]:
    captures = workspace.captures()
    for fact in facts:
        workspace.company(fact.company_id)
        if fact.source_id not in captures:
            raise ValueError(f"Unknown source for {fact.metric}")
        if captures[fact.source_id].get("kind") == "x":
            raise ValueError("Financial facts require a primary/non-social source; use X as a lead")
        if captures[fact.source_id].get("completeness") != "complete":
            raise ValueError("Financial facts require a complete capture")
    result = []
    for fact in facts:
        data = fact.model_dump(mode="json")
        fact_id = digest(data)
        path = workspace.root / "state/facts" / f"{fact_id}.json"
        if not path.exists():
            write_json(path, {**data, "id": fact_id, "recorded_at": now()})
        result.append(fact_id)
    return result


def add_recommendation(workspace: Workspace, value: Recommendation) -> str:
    company = workspace.company(value.company_id)
    sources = workspace.captures()
    if set(value.source_ids) - sources.keys():
        raise ValueError("Recommendation cites an unknown source")
    if value.action != "insufficient evidence":
        if not value.source_ids or not value.model_path or not value.price or not value.price_date:
            raise ValueError("Actionable views require sources, model, and dated price")
        model_path = workspace.inside(value.model_path)
        model = read_json(model_path)
        if not model:
            raise ValueError("Model output missing")
        if model.get("company_id") != value.company_id:
            raise ValueError("Model belongs to a different company")
        if model.get("currency") != company.currency:
            raise ValueError("Actionable model and quoted price must use the company's trading currency")
        if model.get("synthetic"):
            raise ValueError("Synthetic example models cannot justify an investment recommendation")
        if model.get("purpose") == "illustrative_sensitivity":
            raise ValueError("Illustrative sensitivity models cannot justify actionable investment views")
        from .models import analyse, validate_model

        inputs = read_json(model_path.parent / "inputs.json")
        if not inputs or model_path.name != "model.json":
            raise ValueError("Recommendation requires a generated model.json and its inputs.json snapshot")
        validate_model(inputs)
        expected = analyse(inputs)
        if model.get("authority") == "excel":
            from .excel import verify_snapshot
            verify_snapshot(model_path)
        elif inputs.get("synthetic") or any(model.get(k) != v for k, v in expected.items()):
            raise ValueError("Model output does not reproduce from its validated input snapshot")
        if (
            inputs.get("reference_price") != value.price
            or inputs.get("quote_date") != value.price_date.isoformat()
        ):
            raise ValueError("Recommendation price/date must match the model input snapshot")
    data = value.model_dump(mode="json")
    rec_id = digest(data)
    path = workspace.root / "state/recommendations" / f"{rec_id}.json"
    if not path.exists():
        write_json(path, {**data, "id": rec_id, "recorded_at": now()})
    dossier(workspace, value.company_id)
    return rec_id


def link(path: Path, parent: Path) -> str:
    return Path(os.path.relpath(path, parent)).as_posix().replace(" ", "%20")


def cell(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def dossier(workspace: Workspace, company_id: str) -> Path:
    company = workspace.company(company_id)
    folder = workspace.root / "companies" / company_id
    captures = workspace.captures()
    facts = sorted(
        [
            read_json(p)
            for p in (workspace.root / "state/facts").glob("*.json")
            if read_json(p)["company_id"] == company_id
        ],
        key=lambda f: f["recorded_at"],
    )
    recs = sorted(
        [
            read_json(p)
            for p in (workspace.root / "state/recommendations").glob("*.json")
            if read_json(p)["company_id"] == company_id
        ],
        key=lambda r: r["recorded_at"],
    )
    runs = sorted(
        [
            read_json(p)
            for p in (workspace.root / "state/runs").glob("*.json")
            if company_id in read_json(p)["company_ids"]
        ],
        key=lambda r: r["started_at"],
    )
    latest = runs[-1] if runs else None
    lines = [
        f"# {company.name} ({company.exchange}:{company.ticker})",
        "",
        f"As of {now()}",
        "",
        f"**View:** {recs[-1]['action'] if recs else 'insufficient evidence — research not yet reviewed'}.",
        f"**Coverage:** {latest['status'] if latest else 'not collected'}.",
        "",
        f"Trading currency: {company.currency}. Reporting currency: {company.reporting_currency}.",
        "",
        f"[Company website]({company.website})",
        "",
        "## Research map",
        "",
        "```mermaid",
        "flowchart LR",
        "  Reports[Company reports] --> Facts[Reported facts]",
        "  Social[X leads] --> Verify[Verify primary evidence]",
        "  Verify --> Thesis[Thesis and catalysts]",
        "  Facts --> Model[Scenarios and valuation]",
        "  Model --> View[Investment view]",
        "  Thesis --> View",
        "```",
        "",
    ]
    if recs:
        rec = recs[-1]
        lines += [
            "## Thesis and recommendation",
            "",
            f"{rec['thesis']}",
            "",
            f"Horizon: {rec['horizon']}. View dated {rec['as_of']}.",
            "",
            f"Confidence: {rec['confidence_rationale']}",
            "",
        ]
        if rec.get("price") is not None:
            lines += [
                f"Reference quote: {rec['price']} {company.currency}, observed {rec['price_date']}.",
                "",
            ]
        for key in (
            "counterarguments",
            "catalysts",
            "entry_conditions",
            "invalidation_conditions",
            "limitations",
        ):
            lines += [f"### {key.replace('_', ' ').capitalize()}", ""]
            lines += [f"- {s}" for s in rec[key]] or ["None recorded."]
            lines += [""]
        lines += ["Evidence: " + ", ".join(f"[source]({captures[s]['url']})" for s in rec["source_ids"]), ""]
        if rec.get("model_path"):
            lines += [f"[Model output]({link(workspace.inside(rec['model_path']), folder)})", ""]
    lines += [
        "## Historical facts and guidance",
        "",
        "Versions are retained; multiple values for the same period may represent restatements or conflicts.",
        "",
        "| Metric | Period | Value | Unit/currency | Basis | Source |",
        "|---|---|---:|---|---|---|",
    ]
    for fact in facts:
        source = captures[fact["source_id"]]
        values = [
            fact["metric"],
            fact["period"],
            fact["value"],
            f"{fact['unit']} {fact.get('currency') or ''}",
            f"{fact['basis']}; {fact['ownership_basis']}",
            f"[p. {fact['page']}]({source['url']})",
        ]
        lines += ["| " + " | ".join(cell(v) for v in values) + " |"]
    if not facts:
        lines += ["| No verified facts imported yet | — | — | — | — | — |"]
    lines += ["", "## Models", ""]
    from .excel import status as excel_status
    for record in excel_status(workspace, company_id):
        model_path = workspace.inside(record["model"])
        model = read_json(model_path)
        lines += [
            f"**Excel / Markdown alignment:** {record['status'].replace('_', ' ')}. "
            f"Last synchronized: {record['synchronized_at']}.", "",
            f"[Read the model analysis]({link(model_path.parent / 'report.md', folder)}) · "
            f"[Detailed Excel snapshot]({link(model_path.parent / 'model.xlsx', folder)}) · "
            f"[Editable working workbook]({link(workspace.inside(record['working_workbook']), folder)})", "",
        ]
        if record["status"] == "current" and model:
            active = model["active_case"]
            lines += [f"Selected {active} case: {model['scenarios'][active]['per_share']:.4f} {model['currency']}/share. "
                      "Model output only; evidence limitations in the linked analysis still apply.", ""]
        else:
            lines += ["**The working workbook is not synchronized.** Linked analysis describes the last validated snapshot. "
                      "Run `invest excel-sync` before using new workbook edits in research conclusions.", ""]
    model_reports = sorted((folder / "models").glob("*/report.md"))
    lines += [f"- [{p.parent.name}]({link(p, folder)})" for p in model_reports] or ["No model run yet."]
    for report in model_reports:
        validations = sorted(report.parent.glob("validation-*.json"))
        if validations:
            latest_check = validations[-1]
            status = read_json(latest_check)["status"]
            lines += [
                f"- Workbook revalidation for {report.parent.name}: **{status}** "
                f"[record]({link(latest_check, folder)})"
            ]
    lines += ["", "## Recent developments", ""]
    seen_events = set()
    for run in runs[-10:]:
        for decision in run.get("decisions", []):
            if (
                decision["company_id"] == company_id
                and decision["material"]
                and decision["capture_id"] not in seen_events
            ):
                seen_events.add(decision["capture_id"])
                source = captures[decision["capture_id"]]
                lines += [
                    f"- **{decision['verification']}**: {decision['summary']} "
                    f"[Source]({source['url']}). {decision['thesis_impact']}"
                ]
    lines += ["", "## Coverage and open questions", ""]
    lines += [f"- {gap}" for gap in company.gaps]
    if latest:
        lines += [f"- {e}" for e in latest["errors"]]
        if latest["status"] == "pending_review":
            lines += ["- Collected evidence awaits agent review; no no-change conclusion is justified."]
        lines += [
            f"- [Latest run receipt]({link(workspace.root / 'state/runs' / (latest['id'] + '.json'), folder)})"
        ]
    else:
        lines += ["- Company sources have not been collected."]
    if (folder / "thesis.md").exists():
        lines += ["", "[Detailed business thesis and counter-thesis](thesis.md)"]
    path = folder / "dossier.md"
    atomic_text(path, "\n".join(lines) + "\n")
    return path
