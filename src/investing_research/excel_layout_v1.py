"""Portable analyst workbook; Excel formulas own the editable valuation surface.

No Excel automation or proprietary runtime is required to create the workbook.
The hidden manifest is an integrity/round-trip contract, not a calculation engine.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell

from .models import COMMON, FCF, MINE, validate_model

MARKER = "investing-excel-v1"
CASES = ("bear", "base", "bull")


def write_excel_model(data: dict, path: Path) -> None:
    """Create a formula-driven active-case model with portable JSON cell mapping."""
    validate_model(data)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = xlsxwriter.Workbook(path, {"strings_to_formulas": False, "strings_to_urls": False})
    wb.set_properties({"title": f"{data['company_id']} | investment model", "author": "Investing Research"})
    wb.set_calc_mode("auto")
    styles = {
        "title": wb.add_format(
            {"bold": True, "font_size": 21, "font_color": "#FFFFFF", "bg_color": "#142D43"}
        ),
        "section": wb.add_format({"bold": True, "font_color": "#FFFFFF", "bg_color": "#28566F"}),
        "text": wb.add_format({"font_color": "#243746", "text_wrap": True, "valign": "top"}),
        "note": wb.add_format({"font_color": "#667085", "text_wrap": True, "valign": "top", "font_size": 10}),
        "money_m": wb.add_format({"bold": True, "font_size": 15, "font_color": "#008000", "num_format": '#,##0.0,,"m"'}),
        "input": wb.add_format(
            {"font_color": "#0000FF", "bg_color": "#F0F5FF", "num_format": '#,##0.00;(#,##0.00);"–"'}
        ),
        "input_text": wb.add_format({"font_color": "#0000FF", "bg_color": "#F0F5FF"}),
        "input_pct": wb.add_format({"font_color": "#0000FF", "bg_color": "#F0F5FF", "num_format": "0.0%"}),
        "formula": wb.add_format({"font_color": "#202020", "num_format": '#,##0.00;(#,##0.00);"–"'}),
        "link": wb.add_format({"font_color": "#008000", "num_format": '#,##0.00;(#,##0.00);"–"'}),
        "pct": wb.add_format({"font_color": "#008000", "num_format": "0.0%"}),
        "year": wb.add_format({"bold": True, "num_format": "0", "bottom": 1}),
        "value": wb.add_format(
            {"bold": True, "font_size": 15, "font_color": "#008000", "num_format": "0.0000"}
        ),
    }
    styles["total"] = wb.add_format({"bold": True, "font_color": "#202020", "bg_color": "#EAF2F5", "top": 1, "top_color": "#AEC5CE", "num_format": '#,##0.00;(#,##0.00);"–"'})
    styles["pass"] = wb.add_format({"bold": True, "font_color": "#176443", "bg_color": "#E6F4EC"})
    styles["fail"] = wb.add_format({"bold": True, "font_color": "#A12232", "bg_color": "#FCE9EC"})
    for fmt in styles.values():
        fmt.set_font_name("Aptos")
    names = (
        "Summary",
        "Assumptions",
        "Historical",
        "Operating",
        "Valuation",
        "Sensitivities",
        "Checks",
        "Readme",
        "_Model",
    )
    sheets = {name: wb.add_worksheet(name) for name in names}
    n = max(len(s["years"]) for s in data["scenarios"].values())
    manifest = {
        "schema_version": 1,
        "baseline": copy.deepcopy(data),
        "inputs": {},
        "outputs": {},
        "formula_cells": {},
    }
    currency = data["currency"]

    def address(row, col):
        return xl_rowcol_to_cell(row, col)

    def ref(sheet, row, col):
        return f"'{sheet}'!{xl_rowcol_to_cell(row, col, True, True)}"

    def formula(sheet, row, col, value, style="formula", output=None):
        cell = address(row, col)
        if sheet == "Operating" and output and output.rsplit("/", 1)[-1] in ("fcf", "present_value", "illustrative_cash"):
            style = "total"
        sheets[sheet].write_formula(row, col, value, styles[style])
        manifest["formula_cells"][f"{sheet}!{cell}"] = value
        if output:
            manifest["outputs"][output] = {"sheet": sheet, "cell": cell}
        return ref(sheet, row, col)

    def input_cell(pointer, row, col, value, unit="", sheet="Assumptions"):
        fmt = "input_pct" if unit == "fraction" else "input_text" if isinstance(value, str) else "input"
        sheets[sheet].write(row, col, value, styles[fmt])
        manifest["inputs"][pointer] = {"sheet": sheet, "cell": address(row, col)}
        record = data.get("provenance", {}).get(pointer)
        if record:
            sheets[sheet].write_comment(row, col, "\n".join(f"{k}: {v}" for k, v in record.items()))
        return ref(sheet, row, col)

    for name, ws in sheets.items():
        ws.hide_gridlines(2)
        ws.set_column("A:A", 43)
        ws.set_column("B:B", 25)
        ws.set_column(2, max(8, n + 1), 17)
        ws.set_default_row(23)
        ws.set_zoom(90)
        ws.set_tab_color("#287F8E" if name in ("Summary", "Assumptions") else "#142D43")
        ws.freeze_panes(6, 2)
        ws.set_landscape()
        ws.set_paper(9)
        ws.fit_to_pages(1, 0)
        ws.set_margins(0.3, 0.3, 0.4, 0.4)
        ws.set_footer("&L" + data["company_id"] + " | " + name + "&RPage &P of &N")
        if name != "_Model":
            ws.merge_range(0, 0, 1, max(5, n + 1), f"{data['company_id']}  /  {name}", styles["title"])
            ws.print_area(0, 0, 45, max(5, n + 1))
    a = sheets["Assumptions"]
    a.write("A4", "Active scenario", styles["section"])
    a.write("B4", "base", styles["input_text"])
    a.data_validation("B4", {"validate": "list", "source": list(CASES)})
    manifest["outputs"]["active_case"] = {"sheet": "Assumptions", "cell": "B4"}
    a.merge_range(
        "C4:H4", "Blue = editable inputs • Green = cross-sheet links • Black = calculations", styles["note"]
    )
    global_refs = {}
    for r, key in enumerate((*COMMON, "reference_price", "valuation_date", "quote_date"), 6):
        a.write(r, 0, key.replace("_", " ").title())
        value = data.get(key)
        unit = (
            "shares"
            if key == "diluted_shares"
            else currency + "/share"
            if key == "reference_price"
            else currency
        )
        if key.endswith("date"):
            unit = "YYYY-MM-DD"
        global_refs[key] = input_cell("/" + key, r, 1, value, unit)
        a.write(r, 2, unit, styles["note"])
    a.merge_range(
        "A15:H16",
        "Enter dates as YYYY-MM-DD text. Blank quote and reference price mean no market comparison. Preserve the declared ownership basis; attributable inputs require ownership = 100%.",
        styles["note"],
    )
    fields = MINE if data["model_type"] == "finite_mine" else FCF
    annual_refs, case_refs = {}, {}
    row = 18
    for name in CASES:
        s = data["scenarios"][name]
        a.merge_range(
            row, 0, row, max(5, n + 1), name.upper() + " / " + s["ownership_basis"], styles["section"]
        )
        case_refs[name] = {}
        for offset, key in enumerate(("discount_rate", "ownership", "residual_value"), 1):
            a.write(row + offset, 0, key.replace("_", " ").title())
            case_refs[name][key] = input_cell(
                f"/scenarios/{name}/{key}",
                row + offset,
                1,
                s[key],
                "fraction" if key != "residual_value" else currency,
            )
        a.write(row + 4, 0, "Explicit forecast periods")
        a.write(row + 4, 1, len(s["years"]))
        case_refs[name]["horizon"] = ref("Assumptions", row + 4, 1)
        for i in range(n):
            a.write(row + 5, i + 2, int(data["valuation_date"][:4]) + i + 1, styles["year"])
        annual_refs[name] = {}
        for j, field in enumerate(fields):
            r = row + 6 + j
            a.write(
                r,
                0,
                "Production proxy (not payable sales)"
                if field == "payable_tonnes" and s.get("volume_basis") == "imputed_production"
                else field.replace("_", " ").title(),
            )
            first = data["provenance"][f"/scenarios/{name}/years/0/{field}"]
            units = {
                data["provenance"][f"/scenarios/{name}/years/{i}/{field}"]["unit"]
                for i in range(len(s["years"]))
            }
            a.write(r, 1, first["unit"] if len(units) == 1 else "see cell provenance", styles["note"])
            annual_refs[name][field] = []
            for i in range(n):
                if i < len(s["years"]):
                    pointer = f"/scenarios/{name}/years/{i}/{field}"
                    unit = data["provenance"][pointer]["unit"]
                    ar = input_cell(pointer, r, i + 2, s["years"][i][field], unit)
                else:
                    a.write(r, i + 2, 0, styles["note"])
                    ar = ref("Assumptions", r, i + 2)
                annual_refs[name][field].append(ar)
        row += 8 + len(fields)
    a.set_portrait()
    a.print_area(0, 0, row - 2, max(5, n + 1))
    a.set_h_pagebreaks([18 + (8 + len(fields)), 18 + 2 * (8 + len(fields))])

    def choose(values):
        return f'IF(Assumptions!$B$4="bear",{values[0]},IF(Assumptions!$B$4="base",{values[1]},{values[2]}))'

    active = {}
    for r, key in enumerate(("discount_rate", "ownership", "residual_value", "horizon"), 3):
        sheets["Operating"].write(r, 0, key.replace("_", " ").title())
        active[key] = formula(
            "Operating",
            r,
            1,
            "=" + choose([case_refs[c][key] for c in CASES]),
            "pct" if key in ("discount_rate", "ownership") else "link",
        )
    sheets["Operating"].write("A8", "Volume basis")
    formula(
        "Operating",
        7,
        1,
        "=" + choose(['"' + data["scenarios"][c].get("volume_basis", "payable_sales") + '"' for c in CASES]),
        "link",
    )
    start = 9
    rows = {key: start + i for i, key in enumerate(fields)}
    calculated = (
        "revenue",
        "operating_cost",
        "royalties",
        "ebit",
        "tax",
        "nopat",
        "operating_fcf",
        "fcf",
        "present_value",
        "illustrative_cash",
    )
    calc_rows = {key: start + len(fields) + 2 + i for i, key in enumerate(calculated)}
    o = sheets["Operating"]
    o.write(8, 0, "Annual end-of-period forecast", styles["section"])
    for key, r in rows.items():
        o.write(r, 0, "Volume (see case basis)" if key == "payable_tonnes" else key.replace("_", " ").title())
        o.write(
            r,
            1,
            "see case input units"
            if key in ("price", "fx")
            else data["provenance"][f"/scenarios/base/years/0/{key}"]["unit"],
            styles["note"],
        )
    for key, r in calc_rows.items():
        o.write(
            r,
            0,
            key.replace("_", " ").title(),
            styles["section"] if key in ("fcf", "present_value") else styles["text"],
        )
        o.write(r, 1, currency, styles["note"])
    for i in range(n):
        col = i + 2
        formula(
            "Operating",
            8,
            col,
            f"=YEAR(DATEVALUE({global_refs['valuation_date']}))+{i + 1}",
            "year",
            f"years/{i}/year",
        )
        refs = {}
        for key, r in rows.items():
            refs[key] = formula(
                "Operating", r, col, "=" + choose([annual_refs[c][key][i] for c in CASES]), "link"
            )
        cr = {key: ref("Operating", r, col) for key, r in calc_rows.items()}
        if data["model_type"] == "finite_mine":
            expressions = {
                "revenue": f"{refs['payable_tonnes']}*{refs['price']}*{refs['fx']}",
                "operating_cost": f"{refs['payable_tonnes']}*{refs['unit_cost']}",
                "royalties": f"{cr['revenue']}*{refs['royalty_rate']}",
                "ebit": f"{cr['revenue']}-{cr['operating_cost']}-{cr['royalties']}-{refs['depreciation']}",
                "tax": f"MAX(0,{cr['ebit']})*{refs['tax_rate']}",
                "nopat": f"{cr['ebit']}-{cr['tax']}",
            }
        else:
            expressions = {key: '""' for key in ("revenue", "operating_cost", "royalties", "ebit", "tax")}
            expressions["nopat"] = refs["nopat"]
        expressions.update(
            {
                "operating_fcf": f"{cr['nopat']}+{refs['depreciation']}-{refs['capex']}-{refs['working_capital_change']}-{refs['closure']}",
                "fcf": f"{cr['operating_fcf']}*{active['ownership']}-{refs['corporate_cost']}+IF({i + 1}={active['horizon']},{active['residual_value']},0)",
                "present_value": f"{cr['fcf']}/(1+{active['discount_rate']})^{i + 1}",
                "illustrative_cash": f"{global_refs['cash'] if i == 0 else ref('Operating', calc_rows['illustrative_cash'], col - 1)}+{cr['fcf']}",
            }
        )
        for key, expression in expressions.items():
            formula("Operating", calc_rows[key], col, "=" + expression, output=f"years/{i}/{key}")
    o.merge_range(
        calc_rows["illustrative_cash"] + 2,
        0,
        calc_rows["illustrative_cash"] + 3,
        max(5, n + 1),
        "Illustrative cash excludes financing, dividends and debt maturities. This is a finite cash-flow schedule, not an integrated three-statement forecast. No terminal perpetuity is assumed.",
        styles["note"],
    )
    o.print_area(0, 0, calc_rows["illustrative_cash"] + 4, max(5, n + 1))
    o.fit_to_pages(1, 1)

    v = sheets["Valuation"]
    end = address(calc_rows["present_value"], n + 1)
    begin = address(calc_rows["present_value"], 2)
    vals = {}
    formulas = {
        "enterprise_value": f"=SUM(Operating!{begin}:{end})",
        "cash": "=" + global_refs["cash"],
        "other_assets": "=" + global_refs["other_assets"],
        "debt": "=" + global_refs["debt"],
        "equity_value": "=B5+B6+B7-B8",
        "diluted_shares": "=" + global_refs["diluted_shares"],
        "per_share": "=B9/B10",
        "minimum_illustrative_cash": f"=MIN({global_refs['cash']},Operating!{address(calc_rows['illustrative_cash'], 2)}:{address(calc_rows['illustrative_cash'], n + 1)})",
    }
    for r, (key, expression) in enumerate(formulas.items(), 4):
        v.write(r, 0, key.replace("_", " ").title())
        vals[key] = formula("Valuation", r, 1, expression, "value" if key == "per_share" else "link", key)
        v.write(
            r,
            2,
            "shares" if key == "diluted_shares" else currency + "/share" if key == "per_share" else currency,
            styles["note"],
        )
    v.write("A15", "Reference price")
    formula(
        "Valuation",
        14,
        1,
        f'=IF({global_refs["reference_price"]}="","Unavailable",{global_refs["reference_price"]})',
        "link",
    )
    v.write("A16", "Model / reference price − 1")
    formula("Valuation", 15, 1, '=IF(AND(ISNUMBER(B15),B15>0),B11/B15-1,"Unavailable")', "pct")
    v.merge_range(
        "A19:F21",
        "This is a model output, not a price target or investment recommendation. Corporate costs and residual value are company-attributable; operating cash flows apply ownership once. Residual value is explicit, not a perpetuity.",
        styles["note"],
    )

    se = sheets["Sensitivities"]
    driver = "Price" if data["model_type"] == "finite_mine" else "NOPAT"
    se.merge_range(
        "A4:F5",
        f"{driver} multiplier × discount rate / {currency} per share. All active-case forecast years recomputed, including positive-EBIT tax floor.",
        styles["note"],
    )
    for j, shift in enumerate((-0.02, 0, 0.02), 2):
        formula(
            "Sensitivities",
            6,
            j,
            f"=MAX(0,{active['discount_rate']}+({shift}))",
            "pct",
            f"discount_rate/{j - 2}",
        )
    for r, multiplier in enumerate((0.8, 1.0, 1.2), 7):
        se.write(r, 1, multiplier, styles["formula"])
        manifest["outputs"][f"driver_multiplier/{r - 7}"] = {"sheet": "Sensitivities", "cell": address(r, 1)}
        for j in range(2, 5):
            helper_row = 16 + (r - 7) * 3 + j - 2
            se.write(helper_row, 0, f"Driver {multiplier:.1f}× / rate column {j - 1}", styles["note"])
            for i in range(n):
                x = {k: ref("Operating", rr, i + 2) for k, rr in rows.items()}
                mult = f"$B${r + 1}"
                if data["model_type"] == "finite_mine":
                    revenue = f"({x['payable_tonnes']}*{x['price']}*{x['fx']}*{mult})"
                    ebit = f"({revenue}*(1-{x['royalty_rate']})-{x['payable_tonnes']}*{x['unit_cost']}-{x['depreciation']})"
                    nopat = f"({ebit}-MAX(0,{ebit})*{x['tax_rate']})"
                else:
                    nopat = f"({x['nopat']}*{mult})"
                fcf = f"(({nopat}+{x['depreciation']}-{x['capex']}-{x['working_capital_change']}-{x['closure']})*{active['ownership']}-{x['corporate_cost']}+IF({i + 1}={active['horizon']},{active['residual_value']},0))"
                formula("Sensitivities", helper_row, i + 2, f"={fcf}/(1+{address(6, j)})^{i + 1}", "link")
            expression = f"=(SUM({address(helper_row, 2)}:{address(helper_row, n + 1)})+{global_refs['cash']}+{global_refs['other_assets']}-{global_refs['debt']})/{global_refs['diluted_shares']}"
            formula("Sensitivities", r, j, expression, "value", f"sensitivity/{r - 7}/{j - 2}")
    se.write("A15", "Auditable discounted-cash-flow helpers", styles["section"])
    se.conditional_format("C8:E10", {"type": "3_color_scale"})

    h = sheets["Historical"]
    headers = (
        "Metric",
        "Period",
        "Value",
        "Unit",
        "Currency",
        "Basis / ownership",
        "Published",
        "Source",
        "Page",
    )
    for col, label in enumerate(headers):
        h.write(5, col, label, styles["section"])
    for r, fact in enumerate(data["historical"], 6):
        values = (
            fact["metric"],
            fact["period"],
            fact["value"],
            fact["unit"],
            fact["currency"] or "",
            f"{fact['basis']} / {fact['ownership_basis']}",
            fact["publication_date"],
            fact["source"],
            str(fact["page"]),
        )
        for col, value in enumerate(values):
            h.write(r, col, value, styles["formula"] if col == 2 else styles["text"])
        h.set_row(r, 42)
        if str(fact["source"]).startswith(("https://", "http://")):
            h.write_url(r, 7, fact["source"], string="Open source report")
    h.merge_range(
        "A4:I4",
        "Source-linked reported facts. Historical coverage may be incomplete; no integrated statements are inferred.",
        styles["note"],
    )
    h.set_column("A:A", 48)
    h.set_column("B:B", 18)
    h.set_column("F:F", 26)
    h.set_column("H:H", 24)
    h.repeat_rows(0, 5)
    h.autofilter(5, 0, max(6, len(data["historical"]) + 5), 8)
    h.print_area(0, 0, max(8, len(data["historical"]) + 5), 8)

    ch = sheets["Checks"]
    checks = [
        (
            "Valid active scenario",
            '=IF(OR(Assumptions!B4="bear",Assumptions!B4="base",Assumptions!B4="bull"),"PASS","FAIL")',
        ),
        ("Positive diluted shares", f'=IF({global_refs["diluted_shares"]}>0,"PASS","FAIL")'),
        (
            "Equity bridge reconciliation",
            '=IF(ABS(Valuation!B9-(Valuation!B5+Valuation!B6+Valuation!B7-Valuation!B8))<0.01,"PASS","FAIL")',
        ),
        (
            "Central sensitivity reconciliation",
            '=IF(ABS(Sensitivities!D9-Valuation!B11)<0.000001,"PASS","FAIL")',
        ),
        (
            "Reference quote pair",
            f'=IF(OR(AND({global_refs["reference_price"]}="",{global_refs["quote_date"]}=""),AND(ISNUMBER({global_refs["reference_price"]}),{global_refs["reference_price"]}>0,{global_refs["quote_date"]}<>"")),"PASS","FAIL")',
        ),
        ("Ownership range", f'=IF(AND({active["ownership"]}>=0,{active["ownership"]}<=1),"PASS","FAIL")'),
    ]
    for r, (label, expression) in enumerate(checks, 4):
        ch.write(r, 0, label)
        formula("Checks", r, 1, expression, output=f"checks/{r - 4}")
    ch.conditional_format("B5:B10", {"type": "text", "criteria": "containing", "value": "PASS", "format": styles["pass"]})
    ch.conditional_format("B5:B10", {"type": "text", "criteria": "containing", "value": "FAIL", "format": styles["fail"]})
    ch.merge_range(
        "A13:F15",
        "Workbook checks are structural, not evidence approval. Import validates all scenarios, declared units, formula integrity and financial constraints independently. Any formula changes require a new model design review.",
        styles["note"],
    )

    s = sheets["Summary"]
    s.merge_range(
        "A4:H5",
        "SYNTHETIC EXAMPLE"
        if data.get("synthetic")
        else "ILLUSTRATIVE SENSITIVITY — not an actionable valuation"
        if data.get("purpose") == "illustrative_sensitivity"
        else "Evidence-bound valuation — review assumptions and limitations",
        styles["section"],
    )
    for r, (label, key) in enumerate(
        (
            ("Active scenario", None),
            ("Model value per share", "per_share"),
            ("Equity value", "equity_value"),
            ("Minimum illustrative cash", "minimum_illustrative_cash"),
        ),
        6,
    ):
        s.write(r, 0, label)
        formula("Summary", r, 1, "=Assumptions!B4" if key is None else "=" + vals[key], "money_m" if key in ("equity_value", "minimum_illustrative_cash") else "value")
    s.merge_range(
        "A12:H14",
        "Markdown is the main research narrative. Use this workbook to inspect and edit detailed assumptions; recalculate in Excel or LibreOffice, save, then import to publish a validated snapshot back to the research memo.",
        styles["text"],
    )
    limitations = data.get("known_limitations", [])
    s.merge_range(
        "A16:H19",
        "Known limitations: "
        + (
            " • ".join(limitations[:2]) + " See Readme for the full limitations register."
            or "Only supplied assumptions are represented. Review Readme and provenance comments."
        ),
        styles["note"],
    )
    for chart_index, key in enumerate(("fcf", "illustrative_cash")):
        chart = wb.add_chart({"type": "column" if chart_index == 0 else "line"})
        chart.add_series(
            {
                "name": "Attributable free cash flow" if chart_index == 0 else "Illustrative cash balance",
                "categories": ["Operating", 8, 2, 8, n + 1],
                "values": ["Operating", calc_rows[key], 2, calc_rows[key], n + 1],
                "fill": {"color": "#287F8E"},
                "line": {"color": "#287F8E"},
            }
        )
        chart.set_title(
            {
                "name": "Attributable free cash flow"
                if chart_index == 0
                else "Illustrative cash — excludes financing"
            }
        )
        chart.set_y_axis({"name": currency, "num_format": '#,##0,,"m"'})
        chart.set_legend({"none": True})
        chart.set_size({"width": 540, "height": 300})
        chart.set_chartarea({"border": {"none": True}, "fill": {"color": "#F6F9FB"}})
        chart.set_title({"name": "Attributable free cash flow" if chart_index == 0 else "Illustrative cash — excludes financing", "name_font": {"size": 12, "color": "#142D43"}})
        s.insert_chart(21, chart_index * 4, chart)
    s.print_area(0, 0, 35, 8)
    s.fit_to_pages(1, 1)
    readme = sheets["Readme"]
    readme.set_portrait()
    paragraphs = [
        "WORKFLOW | Read the Markdown memo first. Excel is the editable detailed model. Change blue assumptions, recalculate, save and import to create a new validated research snapshot. Existing snapshots remain immutable.",
        "MODEL | One active scenario drives all formulas. Select bear/base/bull in Assumptions!B4. Forecast horizons are fixed by the source model; shorter cases have zero inputs after their final period.",
        "UNITS | Calculations use absolute currency amounts, not millions. Input provenance comments identify unit, source, author and rationale. Historical rows retain original reported units; normalize before using them in assumptions.",
        "OWNERSHIP | Whole-operation cash flow is multiplied by ownership once. Corporate costs and residual value are company-attributable. Cash, debt and other assets are added at company level.",
        "METHOD | Annual end-period discounting; explicit residual only. Positive EBIT tax floor; no deferred tax or loss carryforwards. Cash excludes debt repayment, funding and dividends. This is not an integrated income statement, balance sheet and cash-flow forecast.",
        "EDITING | Blue inputs are editable. Green formulas link sheets. Black formulas calculate locally. Keep formulas and metadata intact. Synchronization records changed inputs as analyst overrides. Explain their source and rationale in the research memo; formula edits are rejected.",
        "EVIDENCE | A professional workbook layout does not upgrade uncertain evidence. Missing current quotes, mine-life support, payable sales or capital structure remain research gaps. Model values are not recommendations.",
    ]
    for i, paragraph in enumerate(paragraphs):
        readme.merge_range(4 + i * 4, 0, 6 + i * 4, 7, paragraph, styles["text"])
    start = 4 + len(paragraphs) * 4
    readme.merge_range(start, 0, start, 7, "KNOWN LIMITATIONS", styles["section"])
    for i, limitation in enumerate(limitations):
        readme.merge_range(start + 2 + i * 4, 0, start + 4 + i * 4, 7, limitation, styles["text"])
    readme.print_area(0, 0, start + 4 + len(limitations) * 4, 7)
    metadata = sheets["_Model"]
    metadata.write_string(0, 0, MARKER)
    payload = json.dumps(manifest, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    for i in range(0, len(payload), 30000):
        metadata.write_string(i // 30000 + 1, 0, payload[i : i + 30000])
    metadata.hide()
    wb.close()
