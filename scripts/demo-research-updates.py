"""Run a synthetic append/update journey. No network, credentials or real investment claims."""

import argparse
from pathlib import Path

from investing_research.contracts import Company, Settings
from investing_research.excel import create, synchronize
from investing_research.funding import review as funding_review
from investing_research.model_review import review as model_review
from investing_research.research import append, rebuild
from investing_research.reports import dossier
from investing_research.workspace import Workspace, read_json, write_json

parser = argparse.ArgumentParser()
parser.add_argument("--root", type=Path, default=Path("private/research-demo"))
args = parser.parse_args()
repo = Path(__file__).resolve().parents[1]
ws = Workspace(args.root)
with ws.lock():
    if not ws.settings_path.exists():
        company = Company(
            id="demo-mine",
            name="Synthetic Mine",
            exchange="DEMO",
            ticker="MINE",
            currency="AUD",
            reporting_currency="AUD",
            sector="mining",
            website="https://example.com",
        )
        write_json(ws.settings_path, Settings(companies=[company]).model_dump(mode="json"))
    first = append(ws, read_json(repo / "examples/research/pillar.json"))
    append(
        ws,
        {
            **first["data"],
            "previous": first["id"],
            "status": "weakening",
            "expectation": "Unit cost now assumed at 55 AUD/tonne",
            "rationale": "Synthetic new assumption; original expectation must remain visible.",
        },
    )
    catalyst = append(ws, read_json(repo / "examples/research/catalyst.json"))
    append(
        ws,
        {
            **catalyst["data"],
            "previous": catalyst["id"],
            "event_date": "2026-10-20",
            "rationale": "Synthetic date revision; earlier estimated date remains in history.",
        },
    )
    models = []
    for name, cash in [("baseline", 100), ("revised", 120)]:
        data = read_json(repo / "examples/model-mine.json")
        data["cash"] = cash
        source = ws.root / f"{name}.json"
        write_json(source, data)
        working = ws.root / f"{name}.xlsx"
        if not working.exists():
            create(source, working)
        models.append(synchronize(ws, working))
    paths = [ws.relative(Path(m["output_dir"]) / "model.json") for m in models]
    update = model_review(
        ws,
        {
            "company_id": "demo-mine",
            "prior_model": paths[0],
            "updated_model": paths[1],
            "rationale": "Synthetic example: cash assumption increases from 100 to 120 AUD. No actual reported quarter is claimed.",
            "actuals": [],
        },
    )
    funding = funding_review(
        ws,
        {
            "company_id": "demo-mine",
            "model": paths[1],
            "rationale": "Synthetic financing example: explicit new equity and debt repayments; this is not MLX data.",
            "scenarios": {
                case: [
                    {
                        "year": y["year"],
                        "interest_rate": 0.1,
                        "debt_raised": 0,
                        "debt_repaid": 1,
                        "equity_raised": 10,
                        "issue_price": 2,
                        "dividends": 1,
                        "minimum_cash": 100,
                        "source": "synthetic://demo-financing",
                        "rationale": "Deliberately synthetic terms for exercising cash and share schedules",
                    }
                    for y in scenario["years"]
                ]
                for case, scenario in data["scenarios"].items()
            },
        },
    )
    rebuild(ws, "demo-mine")
    dossier(ws, "demo-mine")
    write_json(
        ws.root / "demo-manifest.json",
        {"baseline": paths[0], "revised": paths[1], "update": update["report"], "funding": funding["report"]},
    )
print(ws.root / "companies/demo-mine/dossier.md")
