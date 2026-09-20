"""Editable formula workbook and independent LibreOffice recalculation."""

from __future__ import annotations
import shutil
import subprocess
import tempfile
from pathlib import Path
import math


def write_workbook(data, result, path):
    import xlsxwriter
    from xlsxwriter.utility import xl_col_to_name
    from .models import MINE, FCF

    with xlsxwriter.Workbook(str(path), {"strings_to_formulas": False, "strings_to_urls": False}) as book:
        blue = book.add_format({"font_color": "#135DA6", "num_format": "0.0000"})
        heading = book.add_format({"bold": True, "bg_color": "#DDEBF7"})
        summary = book.add_worksheet("Summary")
        summary.write_row(
            0, 0, ["Scenario", "Enterprise value", "Equity value", "Per share", "Min cash"], heading
        )
        summary.set_column(0, 5, 24)
        summary.write(
            5,
            0,
            "ILLUSTRATIVE SENSITIVITY ONLY"
            if data.get("purpose") == "illustrative_sensitivity"
            else "Explicit input valuation",
        )
        summary.write(6, 0, "Reference price")
        if data.get("reference_price") is None:
            summary.write_blank(6, 1, None, blue)
            summary.write(7, 0, "Quote unavailable; no market comparison")
        else:
            summary.write_number(6, 1, data["reference_price"], blue)
            summary.write(7, 0, f"Quote date: {data['quote_date']}")
        notes = book.add_worksheet("Readme")
        notes.set_column(0, 0, 110)
        for i, text in enumerate(
            [
                "Blue cells are editable inputs. Formula cells recalculate in Excel/LibreOffice.",
                f"{data['company_id']} | {data['currency']} | as of {data['valuation_date']}",
                "SYNTHETIC demonstration"
                if data.get("synthetic")
                else "Supplied data; verify source provenance.",
                "Full assumptions/source records are in inputs.json and report.md beside this file.",
                "All cash flows are annual period-end; residual is explicit and attributable.",
                "Cash path excludes financing, debt service and distributions.",
                "Mine tax simplified: positive current-year EBIT times tax rate.",
                "Revenue currency conversion: model currency per price-currency unit.",
            ]
        ):
            notes.write(i, 0, text)
        provenance = book.add_worksheet("Provenance")
        provenance.write_row(0, 0, ["Input", "Unit", "Source", "Rationale", "Author"], heading)
        for r, (pointer, record) in enumerate(data["provenance"].items(), 1):
            provenance.write_row(
                r, 0, [pointer] + [record[k] for k in ("unit", "source", "rationale", "author")]
            )
        provenance.set_column(0, 4, 35)
        for index, (name, scenario) in enumerate(data["scenarios"].items(), 1):
            ws = book.add_worksheet(name)
            ws.freeze_panes(11, 1)
            ws.set_column(0, 30, 19)
            for r, (label, value) in enumerate(
                [
                    ("Cash", data["cash"]),
                    ("Debt", data["debt"]),
                    ("Other assets", data["other_assets"]),
                    ("Diluted shares", data["diluted_shares"]),
                    ("Discount rate", scenario["discount_rate"]),
                    ("Ownership", scenario["ownership"]),
                    ("Residual value", scenario["residual_value"]),
                ],
                1,
            ):
                ws.write(r, 0, label)
                ws.write_number(r, 1, value, blue)
            fields = list(MINE if data["model_type"] == "finite_mine" else FCF)
            outputs = [
                "revenue",
                "operating_cost",
                "royalties",
                "ebit",
                "tax",
                "nopat_calc",
                "operating_fcf",
                "fcf",
                "present_value",
                "illustrative_cash",
            ]
            columns = ["year"] + fields + outputs
            headers = [
                "production_tonnes_proxy"
                if key == "payable_tonnes" and scenario.get("volume_basis") == "imputed_production"
                else key
                for key in columns
            ]
            ws.write_row(10, 0, headers, heading)
            for offset, year in enumerate(scenario["years"]):
                row = 11 + offset
                er = row + 1
                ws.write_number(row, 0, year["year"], blue)
                for c, key in enumerate(fields, 1):
                    ws.write_number(row, c, year[key], blue)

                def ref(key):
                    return f"{xl_col_to_name(columns.index(key))}{er}"

                formulas = {}
                if data["model_type"] == "finite_mine":
                    formulas.update(
                        revenue=f"{ref('payable_tonnes')}*{ref('price')}*{ref('fx')}",
                        operating_cost=f"{ref('payable_tonnes')}*{ref('unit_cost')}",
                        royalties=f"{ref('revenue')}*{ref('royalty_rate')}",
                        ebit=f"{ref('revenue')}-{ref('operating_cost')}-{ref('royalties')}-{ref('depreciation')}",
                        tax=f"MAX(0,{ref('ebit')})*{ref('tax_rate')}",
                        nopat_calc=f"{ref('ebit')}-{ref('tax')}",
                    )
                else:
                    formulas["nopat_calc"] = ref("nopat")
                formulas["operating_fcf"] = (
                    f"{ref('nopat_calc')}+{ref('depreciation')}-{ref('capex')}-{ref('working_capital_change')}-{ref('closure')}"
                )
                formulas["fcf"] = f"{ref('operating_fcf')}*$B$7-{ref('corporate_cost')}" + (
                    "+$B$8" if offset == len(scenario["years"]) - 1 else ""
                )
                formulas["present_value"] = f"{ref('fcf')}/(1+$B$6)^{offset + 1}"
                previous_cash = (
                    "$B$2" if offset == 0 else f"{xl_col_to_name(columns.index('illustrative_cash'))}{er - 1}"
                )
                formulas["illustrative_cash"] = f"{previous_cash}+{ref('fcf')}"
                for key in outputs:
                    if key in formulas:
                        expected_key = "nopat" if key == "nopat_calc" else key
                        ws.write_formula(
                            row,
                            columns.index(key),
                            "=" + formulas[key],
                            None,
                            result["scenarios"][name]["years"][offset][expected_key],
                        )
            last = 11 + len(scenario["years"])
            pv_col = xl_col_to_name(columns.index("present_value"))
            cash_col = xl_col_to_name(columns.index("illustrative_cash"))
            resultrow = last + 2
            expressions = [
                f"SUM({pv_col}12:{pv_col}{last})",
                f"B{resultrow + 1}+$B$2+$B$4-$B$3",
                f"B{resultrow + 2}/$B$5",
                f"MIN($B$2,{cash_col}12:{cash_col}{last})",
            ]
            for offset, (key, expression) in enumerate(
                zip(
                    ("enterprise_value", "equity_value", "per_share", "minimum_illustrative_cash"),
                    expressions,
                )
            ):
                ws.write(resultrow + offset, 0, key)
                ws.write_formula(
                    resultrow + offset, 1, "=" + expression, None, result["scenarios"][name][key]
                )
                summary.write_formula(
                    index,
                    offset + 1,
                    f"='{name}'!B{resultrow + offset + 1}",
                    None,
                    result["scenarios"][name][key],
                )
            summary.write(index, 0, name)


def verify_workbook(path: Path, result: dict) -> dict:
    binary = shutil.which("soffice")
    if not binary:
        return {
            "status": "unverified",
            "reason": "LibreOffice/soffice unavailable; cached formula values are not independent recalculation",
        }
    import openpyxl

    with tempfile.TemporaryDirectory(prefix="investing-workbook-") as directory:
        root = Path(directory)
        profile = (root / "profile").as_uri()
        try:
            completed = subprocess.run(
                [
                    binary,
                    f"-env:UserInstallation={profile}",
                    "--headless",
                    "--convert-to",
                    "xlsx",
                    "--outdir",
                    str(root),
                    str(path.resolve()),
                ],
                capture_output=True,
                timeout=90,
            )
            recalculated = root / path.name
            if completed.returncode or not recalculated.exists():
                return {"status": "unverified", "reason": "LibreOffice conversion failed"}
            workbook = openpyxl.load_workbook(recalculated, data_only=True)
            sheet = workbook["Summary"]
            try:
                # JSON canonicalization can change dictionary order. Workbook identity
                # comes from the visible scenario label, never the result iteration order.
                rows_by_name = {}
                for row in range(2, 2 + len(result["scenarios"])):
                    name = sheet.cell(row, 1).value
                    if name in rows_by_name:
                        raise ValueError(f"Duplicate workbook scenario label: {name!r}")
                    rows_by_name[name] = row
                if set(rows_by_name) != set(result["scenarios"]):
                    raise ValueError("Workbook scenario labels do not match expected scenarios")
                for name, expected in result["scenarios"].items():
                    row = rows_by_name[name]
                    for col, key in enumerate(
                        ("enterprise_value", "equity_value", "per_share", "minimum_illustrative_cash"), 2
                    ):
                        value = sheet.cell(row, col).value
                        # Per-share values require a tighter tolerance than whole-currency totals.
                        tolerance = max(1e-8 if key == "per_share" else 1, abs(expected[key]) * 0.0001)
                        if (
                            not isinstance(value, (int, float))
                            or not math.isfinite(value)
                            or abs(value - expected[key]) > tolerance
                        ):
                            raise ValueError(
                                f"Workbook parity failed for {name}/{key}: {value!r} versus {expected[key]}"
                            )
            finally:
                workbook.close()
            return {
                "status": "passed",
                "engine": "LibreOffice",
                "checks": "All scenario EV/equity/per-share/minimum cash recalculated independently",
            }
        except (subprocess.TimeoutExpired, OSError):
            return {"status": "unverified", "reason": "LibreOffice unavailable or timed out"}
