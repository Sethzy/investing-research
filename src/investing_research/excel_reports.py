"""Readable Markdown views of validated Excel snapshots."""


def report(data, result):
    case = result["active_case"]
    currency = data["currency"]
    active = result["scenarios"][case]
    title = data["company_id"].upper().replace("-", ":", 1)
    evidence = "Synthetic worked example" if data.get("synthetic") else "Illustrative sensitivity; valuation evidence remains incomplete" if data.get("purpose") == "illustrative_sensitivity" else "Valuation from disclosed inputs and explicit assumptions"
    lines = [
        f"# {title} — model analysis", "",
        f"**As of {data['valuation_date']} · {case.title()} case · {currency}**", "",
        f"**Evidence status:** {evidence}.", "",
        f"The selected case produces **{active['per_share']:.4f} {currency}/share**. This is a model result, not an investment recommendation.", "",
        "**[Open the detailed Excel model](model.xlsx)** — historical evidence, editable assumptions, operating schedules, equity bridge, charts and live sensitivities.", "",
        f"Excel recalculated and independently checked on {result['synchronized_at']}. This memo describes snapshot `{result['run_id']}`; later workbook edits require `invest excel-sync` to create a new report.", "",
        "## Scenario results", "",
        "All three cases were recalculated in the workbook. Amounts below are in millions except per-share values.", "",
        "| Case | Enterprise value | Equity value | Per share | Minimum illustrative cash |",
        "|---|---:|---:|---:|---:|",
    ]
    for name in ("bear", "base", "bull"):
        row = result["scenarios"][name]
        lines.append(f"| {name.title()} | {row['enterprise_value']/1e6:,.2f} | {row['equity_value']/1e6:,.2f} | {row['per_share']:.4f} | {row['minimum_illustrative_cash']/1e6:,.2f} |")
    lines += ["", "The workbook opens in the selected case. Its selector updates the detailed operating model, valuation, charts and sensitivity matrix.", "", "## What drives the result", ""]
    scenario = data["scenarios"][case]
    lines += [
        f"- Explicit forecast: {scenario['years'][0]['year']}–{scenario['years'][-1]['year']}; discount rate {scenario['discount_rate']:.1%}.",
        f"- Ownership applied to operating cash flows: {scenario['ownership']:.1%}, using the declared {scenario['ownership_basis'].replace('_', ' ')} basis.",
        f"- Equity bridge: discounted attributable cash flows + {data['cash']/1e6:,.2f}m cash + {data['other_assets']/1e6:,.2f}m other assets − {data['debt']/1e6:,.2f}m debt.",
        "- Corporate costs and explicit residual value are company-attributable. The finite-life model has no terminal perpetuity.",
        "- The cash path excludes financing, dividends and debt maturities; it is not a complete liquidity or three-statement forecast.", "",
        "## Selected forecast", "",
        "Amounts in millions of model currency.", "",
        "| Year | Operating free cash flow | Attributable cash flow | Present value | Illustrative cash |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in active["years"]:
        lines.append(f"| {row['year']} | {row['operating_fcf']/1e6:,.2f} | {row['fcf']/1e6:,.2f} | {row['present_value']/1e6:,.2f} | {row['illustrative_cash']/1e6:,.2f} |")
    lines += ["", "## Sensitivity", "", "Base-case driver × discount rate; per-share results read from recalculated Excel.", "", "| Driver multiplier | Discount rate | Per share |", "|---:|---:|---:|"]
    for row in result["sensitivity"]:
        lines.append(f"| {row['driver_multiplier']:.1f}× | {row['discount_rate']:.1%} | {row['per_share']:.4f} |")
    lines += ["", "## Evidence and limitations", ""]
    sources = sorted({row["source"] for row in data["historical"] if row["source"].startswith("https://")})
    for index, url in enumerate(sources, 1):
        lines.append(f"- [Company source {index}]({url}); dates, physical pages, units and reporting bases are recorded in the workbook's Historical sheet.")
    lines.extend("- " + item for item in data.get("known_limitations", []))
    if data.get("reference_price") is None:
        lines.append("- Current reference quote unavailable: no upside/downside versus market or reverse-valuation conclusion is presented.")
    lines += ["", "## Changes and audit trail", ""]
    if result["input_changes"]:
        lines += ["Workbook edits are analyst assumptions; they have not been promoted into reported company facts.", ""]
        for change in result["input_changes"]:
            lines.append(f"- `{change['path']}`: {change['before']} → {change['after']} ({change['sheet']}!{change['cell']}).")
    else:
        lines.append("No input overrides versus this workbook's recorded baseline.")
    lines += ["", f"Snapshot workbook SHA-256: `{result['workbook_sha256']}`.", "", "[Accepted input and provenance snapshot](inputs.json) · [Calculation results and validation](model.json)", ""]
    return "\n".join(lines)
