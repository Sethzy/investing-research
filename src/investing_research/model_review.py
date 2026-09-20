"""Immutable actual-versus-estimate and model revision analysis."""

from pydantic import Field

from .contracts import Record
from .excel import pointer_get, verify_snapshot
from .workspace import atomic_text, digest, now, read_json, write_json


class ActualComparison(Record):
    fact_id: str
    estimate_path: str = Field(pattern=r"^/")
    estimate_period: str
    scale: float = Field(gt=0)
    rationale: str = Field(min_length=1)


class ModelReview(Record):
    company_id: str
    prior_model: str
    updated_model: str
    rationale: str = Field(min_length=1)
    actuals: list[ActualComparison] = Field(default_factory=list)


def review(ws, payload):
    """Caller holds lock. Reviewed model snapshots are immutable inputs, not working copies."""
    request = ModelReview.model_validate(payload)
    ws.company(request.company_id)
    paths = [ws.inside(p) for p in (request.prior_model, request.updated_model)]
    if any(p.name != "model.json" for p in paths):
        raise ValueError("Use immutable model.json snapshots")
    models = [verify_snapshot(p) for p in paths]
    if (
        any(m["company_id"] != request.company_id for m in models)
        or models[0]["currency"] != models[1]["currency"]
    ):
        raise ValueError("Model comparison requires the same company and currency")
    inputs = [read_json(p.parent / "inputs.json") for p in paths]
    if inputs[1]["valuation_date"] < inputs[0]["valuation_date"]:
        raise ValueError("Updated valuation date precedes prior model")
    actuals = []
    captures = ws.captures()
    for row in request.actuals:
        if len(row.fact_id) != 64 or any(c not in "0123456789abcdef" for c in row.fact_id):
            raise ValueError("Invalid fact ID")
        fact = read_json(ws.root / "state/facts" / f"{row.fact_id}.json")
        if not fact or fact["company_id"] != request.company_id or fact["period"] != row.estimate_period:
            raise ValueError("Actual fact company/period must match the estimate comparison")
        source = captures.get(fact["source_id"], {})
        if source.get("kind") == "x" or source.get("completeness") != "complete":
            raise ValueError("Actuals require complete non-social evidence")
        if fact["published_at"] < inputs[0]["valuation_date"]:
            raise ValueError(
                "Actual was already published before the prior model; not an out-of-sample comparison"
            )
        provenance = inputs[0]["provenance"].get(row.estimate_path)
        if (
            not provenance
            or provenance["unit"] != fact["unit"]
            or fact.get("currency") not in (None, inputs[0]["currency"])
        ):
            raise ValueError("Estimate and actual units/currency must match; normalize explicitly first")
        parts = row.estimate_path.strip("/").split("/")
        basis = (
            inputs[0]["scenarios"][parts[1]]["ownership_basis"]
            if parts[0] == "scenarios" and parts[1] in inputs[0]["scenarios"]
            else "consolidated"
        )
        if fact["ownership_basis"] != basis:
            raise ValueError("Actual and estimate ownership basis must match")
        estimate = pointer_get(inputs[0], row.estimate_path)
        if type(estimate) not in (float, int):
            raise ValueError("Estimate path must reference a numeric input")
        estimate *= row.scale
        actuals.append(
            {
                **row.model_dump(),
                "metric": fact["metric"],
                "unit": fact["unit"],
                "estimate": estimate,
                "actual": fact["value"],
                "delta": fact["value"] - estimate,
                "delta_fraction": (fact["value"] - estimate) / abs(estimate) if estimate else None,
                "source": source["url"],
                "page": fact["page"],
            }
        )
    changes = []
    for pointer in sorted(set(inputs[0]["provenance"]) | set(inputs[1]["provenance"])):
        try:
            before, after = (pointer_get(d, pointer) for d in inputs)
        except (KeyError, IndexError, TypeError):
            before, after = "structure changed", "inspect snapshots"
        if before != after:
            changes.append(
                {
                    "path": pointer,
                    "before": before,
                    "after": after,
                    "rationale": inputs[1]["provenance"].get(pointer, {}).get("rationale", "Removed input"),
                }
            )
    identity = digest({"request": request.model_dump(mode="json"), "models": models, "actuals": actuals})
    folder = ws.root / "companies" / request.company_id / "updates" / identity
    result = {
        "id": identity,
        "recorded_at": now(),
        **request.model_dump(mode="json"),
        "actuals": actuals,
        "changes": changes,
        "valuation": {
            case: {
                "before": models[0]["scenarios"][case]["per_share"],
                "after": models[1]["scenarios"][case]["per_share"],
                "delta": models[1]["scenarios"][case]["per_share"]
                - models[0]["scenarios"][case]["per_share"],
            }
            for case in ("bear", "base", "bull")
        },
    }
    if (folder / "review.json").exists():
        previous = read_json(folder / "review.json")
        if any(previous.get(k) != v for k, v in result.items() if k != "recorded_at"):
            raise ValueError("Model review snapshot damaged")
        result = previous
    else:
        write_json(folder / "review.json", result)
    from .reports import cell, link

    lines = [
        f"# {request.company_id} — model update",
        "",
        request.rationale,
        "",
        f"[Prior analysis]({link(paths[0].parent / 'report.md', folder)}) · [Updated analysis]({link(paths[1].parent / 'report.md', folder)})",
        "",
        "## Actuals versus prior estimates",
        "",
        "| Metric / period | Estimate | Actual | Delta | Evidence / scaling |",
        "|---|---:|---:|---:|---|",
    ]
    for a in actuals:
        lines.append(
            "| "
            + " | ".join(
                cell(v)
                for v in (
                    f"{a['metric']} / {a['estimate_period']} ({a['unit']})",
                    a["estimate"],
                    a["actual"],
                    a["delta"],
                    f"[p. {a['page']}]({a['source']}); input × {a['scale']}: {a['rationale']}",
                )
            )
            + " |"
        )
    if not actuals:
        lines += [
            "",
            "No comparable actuals supplied; this is an assumption/model revision, not an earnings-beat claim.",
        ]
    lines += [
        "",
        "## Per-share valuation change",
        "",
        "| Case | Prior | Updated | Change |",
        "|---|---:|---:|---:|",
    ]
    for case, v in result["valuation"].items():
        lines.append(f"| {case} | {v['before']:.4f} | {v['after']:.4f} | {v['delta']:+.4f} |")
    lines += [
        "",
        "Changes include all revised inputs and valuation dates; this table is not an additive causal attribution.",
        "",
        "## Input changes",
        "",
    ]
    lines += [f"- `{c['path']}`: {c['before']} → {c['after']}. {c['rationale']}" for c in changes]
    atomic_text(folder / "report.md", "\n".join(lines) + "\n")
    return {**result, "report": ws.relative(folder / "report.md")}
