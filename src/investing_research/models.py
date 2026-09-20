"""Explicit annual cash-flow models. No data-provider or LLM calls."""

from __future__ import annotations
import copy
import hashlib
import json
import math
from datetime import date
from pathlib import Path

VERSION = "1.2.0"
COMMON = ("cash", "debt", "other_assets", "diluted_shares")
MINE = (
    "payable_tonnes",
    "price",
    "fx",
    "unit_cost",
    "royalty_rate",
    "tax_rate",
    "depreciation",
    "capex",
    "working_capital_change",
    "closure",
    "corporate_cost",
)
FCF = ("nopat", "depreciation", "capex", "working_capital_change", "closure", "corporate_cost")


def number(value, name, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    if minimum is not None and value < minimum or maximum is not None and value > maximum:
        raise ValueError(f"{name} outside permitted range")
    return float(value)


def validate_model(data):
    allowed = set(COMMON) | {
        "company_id",
        "currency",
        "valuation_date",
        "quote_date",
        "reference_price",
        "model_type",
        "provenance",
        "historical",
        "scenarios",
        "known_limitations",
        "synthetic",
        "sector",
        "notes",
        "purpose",
    }
    if set(data) - allowed:
        raise ValueError(f"Unsupported top-level inputs: {sorted(set(data) - allowed)}")
    if data.get("purpose", "valuation") not in ("valuation", "illustrative_sensitivity"):
        raise ValueError("purpose must be valuation or illustrative_sensitivity")
    if not isinstance(data.get("synthetic", False), bool):
        raise ValueError("synthetic must be a boolean")
    if not isinstance(data.get("provenance"), dict):
        raise ValueError("provenance must be an object keyed by input path")
    for pointer, record in data["provenance"].items():
        if not isinstance(record, dict) or not all(
            isinstance(record.get(k), str) and record[k] for k in ("unit", "source", "rationale", "author")
        ):
            raise ValueError(f"Invalid provenance record: {pointer}")
        if not data.get("synthetic", False) and "synthetic://" in record["source"].lower():
            raise ValueError(f"Synthetic provenance requires synthetic=true: {pointer}")
    for key in (
        "company_id",
        "currency",
        "valuation_date",
        "model_type",
        "provenance",
        "historical",
        "scenarios",
    ):
        if key not in data:
            raise ValueError(f"Missing {key}")
    if not isinstance(data.get("known_limitations", []), list) or not all(
        isinstance(x, str) for x in data.get("known_limitations", [])
    ):
        raise ValueError("known_limitations must be a list of strings")
    valuation = date.fromisoformat(data["valuation_date"])
    quote = data.get("quote_date")
    reference = data.get("reference_price")
    if (quote is None) != (reference is None):
        raise ValueError("Supply both reference_price and quote_date, or leave both absent/null")
    if reference is not None:
        if number(reference, "reference_price", 0) <= 0:
            raise ValueError("A verified reference_price must be positive; use null when unavailable")
        if date.fromisoformat(quote) > valuation:
            raise ValueError("Quote date cannot follow valuation date")
    if data["model_type"] not in ("finite_mine", "explicit_fcf"):
        raise ValueError("Unsupported model; select finite_mine or explicit_fcf explicitly")
    if data.get("sector") in ("bank", "insurance"):
        raise ValueError("Banks and insurers need a sector-specific model")
    for key in COMMON:
        number(data.get(key), key, 0)
    if data["diluted_shares"] <= 0:
        raise ValueError("diluted_shares must be positive")
    if set(data["scenarios"]) != {"bear", "base", "bull"}:
        raise ValueError("Supply complete bear, base, bull scenarios")
    for name, scenario in data["scenarios"].items():
        unexpected = set(scenario) - {
            "discount_rate",
            "ownership",
            "ownership_basis",
            "residual_value",
            "years",
            "notes",
            "volume_basis",
        }
        if unexpected:
            raise ValueError(f"Unsupported scenario inputs: {sorted(unexpected)}")
        volume_basis = scenario.get("volume_basis", "payable_sales")
        if volume_basis not in ("payable_sales", "imputed_production"):
            raise ValueError("Unsupported volume_basis")
        if volume_basis == "imputed_production" and data.get("purpose") != "illustrative_sensitivity":
            raise ValueError("Imputed production is only permitted for explicitly illustrative sensitivity")
        number(scenario.get("discount_rate"), "discount_rate", 0, 2)
        number(scenario.get("ownership"), "ownership", 0, 1)
        number(scenario.get("residual_value"), "residual_value", 0)
        if scenario.get("ownership_basis") not in ("whole_operation", "attributable"):
            raise ValueError("Specify ownership_basis")
        if scenario["ownership_basis"] == "attributable" and scenario["ownership"] != 1:
            raise ValueError("Attributable inputs require ownership=1 to prevent double attribution")
        if not isinstance(scenario.get("years"), list) or not scenario["years"]:
            raise ValueError("Each scenario needs explicit forecast years")
        years = scenario["years"]
        for i, year in enumerate(years):
            fields = set(MINE if data["model_type"] == "finite_mine" else FCF) | {"year", "notes"}
            if data["model_type"] == "finite_mine":
                fields.add("price_currency")
            if set(year) - fields:
                raise ValueError(f"Unsupported forecast inputs: {sorted(set(year) - fields)}")
            if year.get("year") != valuation.year + i + 1:
                raise ValueError("Forecast annual periods must start next calendar year and be contiguous")
            for key in MINE if data["model_type"] == "finite_mine" else FCF:
                minimum = None if key in ("nopat", "working_capital_change") else 0
                number(year.get(key), f"{name}/{i}/{key}", minimum)
            if data["model_type"] == "finite_mine":
                if year["fx"] <= 0:
                    raise ValueError("FX (model currency per price currency) must be positive")
                if not year.get("price_currency"):
                    raise ValueError("Each mine year requires price_currency")
                for key in ("royalty_rate", "tax_rate"):
                    number(year[key], key, 0, 1)
    for fact in data["historical"]:
        for key in (
            "entity",
            "metric",
            "value",
            "unit",
            "currency",
            "period",
            "publication_date",
            "source",
            "page",
            "basis",
            "ownership_basis",
        ):
            if key not in fact or (fact[key] is None and key != "currency"):
                raise ValueError(f"Historical fact missing {key}")
        if fact["currency"] is None and fact["unit"] not in (
            "shares",
            "fraction",
            "tonnes",
            "tonnes_tin",
            "percent",
        ):
            raise ValueError("Historical monetary facts require a currency")
        if not data.get("synthetic", False) and "synthetic://" in str(fact["source"]).lower():
            raise ValueError("Synthetic historical sources require synthetic=true")
        number(fact["value"], "historical value")
        if date.fromisoformat(fact["publication_date"]) > valuation:
            raise ValueError("Historical fact published after valuation date")

    # Every scalar financial input must be explicitly sourced or justified.
    def walk(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key not in ("provenance", "historical", "synthetic", "year"):
                    walk(value, path + "/" + key)
        elif isinstance(obj, list):
            for i, value in enumerate(obj):
                walk(value, path + "/" + str(i))
        elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
            record = data["provenance"].get(path, {})
            if not all(record.get(key) for key in ("unit", "rationale", "author", "source")):
                raise ValueError(f"Missing provenance for {path}")
            if not data.get("synthetic", False) and "synthetic://" in str(record["source"]).lower():
                raise ValueError(f"Synthetic provenance requires synthetic=true: {path}")
            key = path.rsplit("/", 1)[-1]
            expected_unit = data["currency"]
            if key in ("ownership", "discount_rate", "royalty_rate", "tax_rate"):
                expected_unit = "fraction"
            elif key == "diluted_shares":
                expected_unit = "shares"
            elif key == "reference_price":
                expected_unit = data["currency"] + "/share"
            elif key == "payable_tonnes":
                expected_unit = "tonnes"
            elif key == "unit_cost":
                expected_unit = data["currency"] + "/tonne"
            elif key in ("price", "fx"):
                parts = path.split("/")
                year = data["scenarios"][parts[2]]["years"][int(parts[4])]
                expected_unit = (
                    year["price_currency"] + "/tonne"
                    if key == "price"
                    else data["currency"] + "/" + year["price_currency"]
                )
                if key == "fx" and year["price_currency"] == data["currency"] and obj != 1:
                    raise ValueError("Same-currency model FX must equal 1")
            if record["unit"] != expected_unit:
                raise ValueError(f"{path} must be normalized to {expected_unit}; got {record['unit']}")

    walk(data)
    return data


def calculate_scenario(data, scenario):
    """End-of-period annual FCFF, explicit residual only, no perpetuity."""
    from financetoolkit.models.intrinsic_model import get_free_cash_flow_to_firm

    ownership = scenario["ownership"]
    rows = []
    liquid = data["cash"]
    for t, year in enumerate(scenario["years"], 1):
        if data["model_type"] == "finite_mine":
            revenue = year["payable_tonnes"] * year["price"] * year["fx"]
            cost = year["payable_tonnes"] * year["unit_cost"]
            royalty = revenue * year["royalty_rate"]
            ebit = revenue - cost - royalty - year["depreciation"]
            tax = max(0, ebit) * year["tax_rate"]
            nopat = ebit - tax
        else:
            revenue = cost = royalty = ebit = tax = None
            nopat = year["nopat"]
        operating_fcf = (
            float(
                get_free_cash_flow_to_firm(
                    nopat, year["depreciation"], year["capex"], year["working_capital_change"]
                )
            )
            - year["closure"]
        )
        fcf = operating_fcf * ownership - year["corporate_cost"]
        if t == len(scenario["years"]):
            fcf += scenario["residual_value"]  # explicitly attributable company-level residual
        pv = fcf / (1 + scenario["discount_rate"]) ** t
        liquid += fcf
        rows.append(
            dict(
                year=year["year"],
                revenue=revenue,
                operating_cost=cost,
                royalties=royalty,
                ebit=ebit,
                tax=tax,
                nopat=nopat,
                operating_fcf=operating_fcf,
                fcf=fcf,
                present_value=pv,
                illustrative_cash=liquid,
            )
        )
    ev = math.fsum(row["present_value"] for row in rows)
    equity = ev + data["cash"] + data["other_assets"] - data["debt"]
    return dict(
        years=rows,
        enterprise_value=ev,
        cash=data["cash"],
        debt=data["debt"],
        other_assets=data["other_assets"],
        equity_value=equity,
        per_share=equity / data["diluted_shares"],
        minimum_illustrative_cash=min([data["cash"]] + [row["illustrative_cash"] for row in rows]),
    )


def scenario_from_base(data, price_multiplier=1.0, cost_multiplier=1.0):
    """Return a separate complete input with base replaced; never mutate the caller."""
    if data["model_type"] != "finite_mine":
        raise ValueError("Price/cost scenario requires a finite_mine model")
    number(price_multiplier, "price multiplier", 0)
    number(cost_multiplier, "cost multiplier", 0)
    result = copy.deepcopy(data)
    for i, year in enumerate(result["scenarios"]["base"]["years"]):
        for key, multiplier in (("price", price_multiplier), ("unit_cost", cost_multiplier)):
            year[key] *= multiplier
            path = f"/scenarios/base/years/{i}/{key}"
            result["provenance"][path]["rationale"] += (
                f"; baseline multiplied by {multiplier}; all forecast years"
            )
            result["provenance"][path]["author"] = "scenario request"
    return result


def analyse(data):
    validate_model(data)
    scenarios = {name: calculate_scenario(data, s) for name, s in data["scenarios"].items()}
    base = data["scenarios"]["base"]
    sensitivity = []
    for multiplier in (0.8, 1.0, 1.2):
        for rate_change in (-0.02, 0.0, 0.02):
            changed = copy.deepcopy(base)
            rate = max(0, base["discount_rate"] + rate_change)
            changed["discount_rate"] = rate
            for year in changed["years"]:
                year["price" if data["model_type"] == "finite_mine" else "nopat"] *= multiplier
            sensitivity.append(
                dict(
                    driver_multiplier=multiplier,
                    discount_rate=rate,
                    per_share=calculate_scenario(data, changed)["per_share"],
                )
            )
    from scipy.optimize import brentq

    def objective(multiplier):
        changed = copy.deepcopy(base)
        for year in changed["years"]:
            year["price" if data["model_type"] == "finite_mine" else "nopat"] *= multiplier
        return calculate_scenario(data, changed)["per_share"] - data["reference_price"]

    try:
        if data.get("reference_price") is None:
            raise ValueError("Missing verified reference price")
        if abs(objective(10) - objective(0)) < 1e-12:
            raise ValueError("Valuation insensitive to selected driver")
        reverse = dict(
            driver="price" if data["model_type"] == "finite_mine" else "nopat",
            multiplier=float(brentq(objective, 0, 10)),
            bounds=[0, 10],
            status="solved",
        )
    except ValueError:
        reverse = dict(
            status="unavailable",
            reason="No verified reference price/quote date supplied"
            if data.get("reference_price") is None
            else "No unique bracketed solution within 0–10× baseline driver",
        )
    comparisons = []
    drivers = (
        ("price", "unit_cost", "payable_tonnes", "fx")
        if data["model_type"] == "finite_mine"
        else ("nopat", "capex")
    )
    for driver in drivers:
        if driver == "fx" and all(year["price_currency"] == data["currency"] for year in base["years"]):
            continue
        for multiplier in (0.8, 1.0, 1.2):
            changed = copy.deepcopy(base)
            for year in changed["years"]:
                if driver == "fx" and year["price_currency"] == data["currency"]:
                    continue
                year[driver] *= multiplier
            value = calculate_scenario(data, changed)["per_share"]
            comparisons.append(
                dict(
                    driver=driver,
                    multiplier=multiplier,
                    per_share=value,
                    change_from_base=value - scenarios["base"]["per_share"],
                )
            )
    return dict(
        model_version=VERSION,
        purpose=data.get("purpose", "valuation"),
        company_id=data["company_id"],
        currency=data["currency"],
        known_limitations=data.get("known_limitations", []),
        valuation_date=data["valuation_date"],
        quote_date=data.get("quote_date"),
        reference_price=data.get("reference_price"),
        synthetic=data.get("synthetic", False),
        scenarios=scenarios,
        sensitivity=sensitivity,
        driver_comparisons=comparisons,
        reverse_valuation=reverse,
        warnings=[
            "Annual end-of-period convention; explicit residual only, no terminal perpetuity.",
            "Cash path excludes financing, dividends and debt maturities; it is not a solvency forecast.",
            "Mine tax is a simplified current-year positive EBIT tax; no tax-loss carryforwards or jurisdiction tax advice.",
        ],
    )


def run_model(input_path: Path, output_dir: Path) -> dict:
    """Write a content-addressed run directory; an existing result is never overwritten."""
    data = json.loads(Path(input_path).read_text())
    result = analyse(data)
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
    digest = hashlib.sha256(canonical + VERSION.encode()).hexdigest()[:16]
    destination = Path(output_dir) / digest
    if destination.exists():
        existing = destination / "model.json"
        if existing.exists():
            return json.loads(existing.read_text())
        raise ValueError(
            f"Incomplete previous model run: {destination}; preserve it and choose another output directory"
        )
    destination.mkdir(parents=True)
    (destination / "inputs.json").write_bytes(canonical)
    result["input_sha256"] = hashlib.sha256(canonical).hexdigest()
    result["run_id"] = digest
    result["output_dir"] = str(destination.resolve())
    from .workbook import write_workbook, verify_workbook

    write_workbook(data, result, destination / "model.xlsx")
    result["workbook_validation"] = verify_workbook(destination / "model.xlsx", result)
    _chart(result, destination)
    (destination / "report.md").write_text(_report(data, result))
    (destination / "model.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return result


def _chart(result, destination):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 4))
    for name, scenario in result["scenarios"].items():
        ax.plot(
            [x["year"] for x in scenario["years"]],
            [x["fcf"] for x in scenario["years"]],
            marker="o",
            label=name,
        )
    ax.set(
        xlabel="Forecast year",
        ylabel=f"Free cash flow ({result['currency']})",
        title="Explicit forecast cash flows",
    )
    ax.legend()
    fig.tight_layout()
    fig.savefig(destination / "cash-flows.svg")
    plt.close(fig)


def _report(data, result):
    lines = [
        f"# {data['company_id']} valuation",
        "",
        f"As of {data['valuation_date']}; reference quote {data.get('quote_date') or 'unavailable — valuation only, no market-price comparison'}.",
        "",
        "**Synthetic demonstration — not a company valuation.**"
        if data.get("synthetic")
        else (
            "**Illustrative sensitivity only — not a reserve-backed or actionable company valuation. Production is an imputed-revenue proxy, not verified payable sales.**"
            if data.get("purpose") == "illustrative_sensitivity"
            else "Coverage: supplied inputs only; see provenance and limitations below."
        ),
        "",
        f"Base value: {result['scenarios']['base']['per_share']:.4f} {data['currency']} per diluted share. This is a model output, not a trade recommendation.",
        "",
        "[Editable workbook](model.xlsx) · [Complete input/provenance snapshot](inputs.json) · [Machine-readable results](model.json)",
        "",
        "## Scenarios",
        "",
        "| Scenario | Enterprise value | Equity value | Per share | Minimum illustrative cash |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, s in result["scenarios"].items():
        lines.append(
            f"| {name} | {s['enterprise_value']:,.2f} | {s['equity_value']:,.2f} | {s['per_share']:.4f} | {s['minimum_illustrative_cash']:,.2f} |"
        )
    lines += [
        "",
        "### Base forecast cash flows",
        "",
        "| Year | Operating free cash flow | Attributable cash flow | Present value | Illustrative cash |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in result["scenarios"]["base"]["years"]:
        lines.append(
            f"| {row['year']} | {row['operating_fcf']:,.2f} | {row['fcf']:,.2f} | {row['present_value']:,.2f} | {row['illustrative_cash']:,.2f} |"
        )
    lines += [
        "",
        "Equity = discounted attributable free cash flows + cash + other assets − debt. Per share = equity ÷ diluted shares.",
        "Corporate costs and residual values are company-attributable; operating cash flows apply the explicitly declared ownership once.",
        "",
        "![Cash flows by scenario](cash-flows.svg)",
        "",
        "Cash-flow trajectories above show the timing and scale of the scenario differences; funding figures exclude financing obligations.",
        "",
        "## Historical facts",
        "",
        "| Metric | Period | Value | Unit | Source/page |",
        "|---|---|---:|---|---|",
    ]
    for fact in data["historical"]:
        lines.append(
            f"| {fact['metric']} | {fact['period']} | {fact['value']} | {fact['unit']} | {fact['source']} / {fact['page']} |"
        )
    if not data["historical"]:
        lines.append(
            "\nHistorical evidence unavailable in this input snapshot; no historical figures inferred."
        )
    lines += [
        "",
        "## Sensitivity",
        "",
        "Driver is tin/commodity price for mines or NOPAT for explicit cash-flow models; all forecast years change together. The unchanged discount-rate row also provides a one-variable driver comparison.",
        "",
        "| Driver multiplier | Discount rate | Per share |",
        "|---:|---:|---:|",
    ]
    for row in result["sensitivity"]:
        lines.append(
            f"| {row['driver_multiplier']:.2f} | {row['discount_rate']:.2%} | {row['per_share']:.4f} |"
        )
    lines += [
        "",
        "## One-variable driver comparisons",
        "",
        "Each change affects only the named input across forecast years; other base inputs remain fixed.",
        "",
        "| Driver | Multiplier | Per share | Change from base |",
        "|---|---:|---:|---:|",
    ]
    for row in result["driver_comparisons"]:
        lines.append(
            f"| {row['driver']} | {row['multiplier']:.2f} | {row['per_share']:.4f} | {row['change_from_base']:+.4f} |"
        )
    lines += [
        "",
        "## Reverse valuation",
        "",
        json.dumps(result["reverse_valuation"]),
        "",
        "## Assumptions and provenance",
        "",
        "| Input path | Unit | Source | Rationale | Author |",
        "|---|---|---|---|---|",
    ]
    for path, record in data["provenance"].items():

        def escape(x):
            return str(x).replace("|", "\\|").replace("\n", " ")

        lines.append(
            "| "
            + " | ".join(
                escape(x)
                for x in (path, record["unit"], record["source"], record["rationale"], record["author"])
            )
            + " |"
        )
    lines += [
        "",
        "## Validation and limitations",
        "",
        f"Workbook recalculation: {result['workbook_validation']['status']}.",
        "",
    ]
    lines.extend("- " + x for x in result["warnings"] + result["known_limitations"])
    return "\n".join(lines) + "\n"
